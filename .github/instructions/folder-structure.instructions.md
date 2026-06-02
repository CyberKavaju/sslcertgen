---
description: "Enforces the PRD-defined folder structure and file naming conventions. Apply when creating any new file or module in the project."
name: "Folder Structure Conventions"
applyTo:
  - "**/*.py"
  - "**/*.html"
  - "**/*.jinja"
---
# Folder Structure Conventions

## App Module Layout

Follow the PRD folder map exactly. Every new file must land in the correct location:

| File type | Location |
|---|---|
| App factory and blueprint registration | `app/__init__.py` |
| Environment-aware config | `app/config.py` |
| Shared extension initialization | `app/extensions.py` |
| Permission constants | `app/permissions.py` |
| SQLAlchemy models | `app/models/<domain>.py` |
| Blueprint route handlers | `app/controllers/<feature>_controller.py` |
| Business logic and orchestration | `app/services/<feature>_service.py` |
| Database query abstractions | `app/repositories/<entity>_repository.py` |
| Flask-WTF form definitions | `app/forms/<feature>_forms.py` |
| Request/response schemas | `app/schemas/<feature>_schema.py` |
| Celery tasks | `app/tasks/<feature>_tasks.py` |
| External provider adapters | `app/tasks/providers/<provider>.py` |
| ETL readers | `app/etl/readers/` |
| ETL validators | `app/etl/validators/` |
| ETL transformers | `app/etl/transformers/` |
| ETL loaders | `app/etl/loaders/` |
| Report builders and metric calculators | `app/reports/<component>.py` |
| Shared helpers | `app/utils/<helper_module>.py` |
| Jinja base templates and layouts | `app/views/layouts/` |
| Feature templates | `app/views/<feature>/` |
| Reusable template macros/fragments | `app/views/components/` |

## Naming Conventions

- Feature-based file names: `<feature>_controller.py`, `<feature>_service.py`, `<feature>_tasks.py`
- Entity-based repository names: `<entity>_repository.py`
- One blueprint per controller file; register it in `app/__init__.py`
- Split files when a module grows beyond a single coherent responsibility; combine when cohesion is high

## Test Mirroring

- Unit tests mirror the `app/` structure under `tests/unit/`
- Integration tests go in `tests/integration/`
- E2E browser tests go in `tests/e2e/`
- Shared pytest fixtures go in `tests/conftest.py`
- Factory files go in `tests/factories/`
- Sample file fixtures (CSV, XLSX, JSON) go in `tests/fixtures/`

## Definition Of Done

- Every new file is in the correct directory for its layer and responsibility.
- File names follow the feature-based or entity-based convention.
- No logic leaks into `__init__.py` files beyond imports and registration.
