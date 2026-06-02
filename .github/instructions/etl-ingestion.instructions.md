---
description: "File ingestion, ETL pipeline, and import job rules. Apply when working on file upload handling, ETL modules, import services, or import controllers."
name: "ETL and Ingestion Pipeline"
applyTo:
  - "app/etl/**/*.py"
  - "app/tasks/**/*.py"
  - "app/services/import*.py"
  - "app/controllers/import*.py"
---
# ETL and Ingestion Pipeline Rules

## File Upload Security

- Call `werkzeug.utils.secure_filename()` on every uploaded filename before storing or referencing it on the filesystem.
- Validate MIME type and file extension server-side against an allowlist (`text/csv`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, etc.).
- Reject files exceeding `MAX_CONTENT_LENGTH` immediately before reading content.
- Never execute or evaluate uploaded file content.

## Checksum and Deduplication

- Compute and store a SHA-256 checksum of the raw file bytes before any processing begins.
- Use the checksum plus source/business keys to detect duplicate uploads before creating a new import job.

## Pipeline Order

ETL must follow this sequence — never skip or reorder steps:

1. **Upload** — store raw file, record `import_files` row, compute checksum
2. **Validate** — check structure, types, required columns; produce row-level validation errors
3. **Map** — apply saved or user-defined column mappings from `import_mappings`
4. **Stage** — write normalized rows to `staging_rows` with validation status
5. **Transform** — apply type coercion, deduplication, business key resolution
6. **Load** — bulk-insert validated rows into canonical tables via PostgreSQL `COPY`
7. **Reconcile** — verify row counts, flag anomalies, update `import_jobs` totals
8. **Audit** — finalize `import_jobs` status, row counts, and error summary

## Row-Level Rejection Logs

- Every rejected row must produce a record in `staging_rows` with `row_number`, `payload_json`, and `validation_errors_json`.
- Never silently drop rejected rows; they must be diagnosable without re-uploading the file.

## Bulk Loading

- Use PostgreSQL `COPY` via psycopg for bulk inserts of validated rows into staging and canonical tables when row volume justifies it.
- Do not use ORM `session.add()` in a loop for bulk loads.

## Async Execution

- Never run ETL pipeline steps synchronously in a route handler.
- Import jobs run as Celery tasks; the route handler creates the `import_jobs` record and dispatches the task, then returns `202 Accepted` with the `job_id`.

## Mapping Templates

- Saved mapping templates (`import_mappings`) are versioned; never mutate an active version in place.
- Create a new version when mappings change; preserve the previous version for replay of historical jobs.

## Definition Of Done

- Uploaded files pass `secure_filename()` and MIME type checks before any processing.
- Checksum is stored before ETL begins.
- All rejected rows are logged with row number and error detail.
- ETL runs as a Celery task; route returns `202 Accepted`.
