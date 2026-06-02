---
description: "Master index of all instruction files. Apply to every file — use this routing table to identify which additional instruction files must be followed for the current task."
name: "Instruction Index"
applyTo:
  - "**"
---
# Instruction Index

This file routes agents to the correct domain-specific instruction file(s) for any task. It contains no rules of its own — only a lookup table.

## Routing Table

| Task type | Instruction file(s) to apply |
|---|---|
| Writing or updating any test | `tdd.instructions.md` |
| Any code touching input, SQL, passwords, secrets, or auth | `security.instructions.md` |
| Adding or modifying a controller, service, or repository | `mvc-layers.instructions.md` |
| Creating any new file or module anywhere in `app/` | `folder-structure.instructions.md` |
| Implementing login, logout, permissions, or access guards | `auth-rbac.instructions.md` + `security.instructions.md` |
| Adding or changing a SQLAlchemy model, migration, or SQL file | `data-model.instructions.md` + `security.instructions.md` |
| Adding or changing an API endpoint or response schema | `api-design.instructions.md` + `mvc-layers.instructions.md` |
| Touching anything under `app/etl/` or import services/controllers | `etl-ingestion.instructions.md` + `security.instructions.md` |
| Touching anything under `app/tasks/` or any async/background flow | `async-tasks.instructions.md` |
| Adding a Jinja template or UI component | `ui-design-system.instructions.md` + `folder-structure.instructions.md` |
| Creating or modifying static CSS or JS | `ui-design-system.instructions.md` |
| Fixing a bug | `tdd.instructions.md` (regression test required) |

## All Available Instruction Files

| File | Scope |
|---|---|
| `tdd.instructions.md` | Red-Green-Refactor, test-first, regression tests |
| `security.instructions.md` | Input validation, SQL safety, secrets, CSRF, password hashing |
| `mvc-layers.instructions.md` | Layer boundaries: controller / service / repository / model |
| `folder-structure.instructions.md` | Directory layout, file naming, test mirroring |
| `auth-rbac.instructions.md` | Permission strings, session vs JWT, per-request authz |
| `data-model.instructions.md` | UUID PKs, TIMESTAMPTZ, NUMERIC money, JSONB limits, Alembic |
| `api-design.instructions.md` | `/api/v1/` prefix, 202 async, rate limits, error contracts |
| `etl-ingestion.instructions.md` | File upload safety, ETL pipeline order, bulk load, audit |
| `async-tasks.instructions.md` | Celery tasks, job status records, retry with backoff |
| `ui-design-system.instructions.md` | Frozen Light glassmorphism tokens, glass classes, layout, components, forbidden patterns |
