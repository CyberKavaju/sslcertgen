---
description: "Celery task conventions, job status tracking, and async execution rules. Apply when working on background tasks, scheduled jobs, or any async flow."
name: "Async Tasks and Background Jobs"
applyTo:
  - "app/tasks/**/*.py"
  - "app/services/**/*.py"
---
# Async Tasks and Background Jobs Rules

## What Must Run Asynchronously

The following operations must always run as Celery tasks — never synchronously in a route handler:

- File import and ETL pipeline execution
- Report run generation
- Export file creation (CSV, XLSX, PDF)
- CRM connector sync jobs
- Scheduled report delivery
- SMS batch dispatch

## Route Handler Responsibility

- The route handler creates the job record (e.g. `import_jobs`, `report_runs`, `export_jobs`), dispatches the Celery task, and immediately returns `202 Accepted` with the `job_id`.
- The route handler must not wait for or poll the task result.

## Job Status Tracking

- Every async job has a corresponding database record with a `status` field updated at each lifecycle event:
  - `pending` — record created, task not yet started
  - `running` — task has begun execution
  - `completed` — task finished successfully
  - `failed` — task encountered an unrecoverable error
- Update `started_at` when the task begins and `finished_at` when it ends (success or failure).
- Record a human-readable `error_summary` on failure.

## Task Organization

- All Celery task functions live in `app/tasks/<feature>_tasks.py`.
- Celery Beat schedule entries are defined in `app/tasks/` (e.g. in a `beat_schedule.py` or within the task module as `app.conf.beat_schedule`).
- Provider adapter clients (SMS, CRM) live in `app/tasks/providers/<provider>.py`.

## Retry Policy

- Tasks that call external providers (SMS, CRM APIs, webhooks) must define a retry policy with exponential backoff.
- Set a `max_retries` limit; do not retry indefinitely.
- Use Celery's `self.retry(exc=exc, countdown=backoff)` pattern.
- Transient network errors should trigger a retry; business logic errors (invalid data) should not.

## Idempotency

- Tasks that mutate database state must be idempotent where feasible — re-running a completed job should not create duplicate records.
- Use the job record's status to guard against duplicate execution.

## Definition Of Done

- Every heavy operation dispatches a Celery task; no synchronous execution in routes.
- Job records are updated at `pending`, `running`, `completed`, and `failed` states.
- External provider calls have retry logic with exponential backoff and a max retry limit.
