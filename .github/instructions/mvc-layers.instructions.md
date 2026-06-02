---
description: "Enforces MVC layer boundaries and service layer separation for Flask. Apply when adding or modifying controllers, services, repositories, or models."
name: "MVC Layer Boundaries"
applyTo:
  - "**/*.py"
---
# MVC Layer Boundaries

## Controller Layer (`app/controllers/`)

- Controllers handle only request parsing, input validation, response shaping, and calling the service layer.
- No business logic, no direct database access, no ORM queries inside controllers.
- Controllers return HTTP responses; they do not compute business outcomes.

## Service Layer (`app/services/`)

- All business logic, orchestration, and workflow rules live in services.
- Services coordinate across multiple repositories, external adapters, and domain objects.
- Services do not import from controllers or handle HTTP concerns (status codes, request objects, response shaping).
- Transactional boundaries and lineage recording belong in the service layer.

## Repository Layer (`app/repositories/`)

- All database access and query logic lives in repositories.
- Repositories work with SQLAlchemy models and return domain objects or raw data — never HTTP constructs.
- No business rules inside repositories; they execute queries, not decisions.

## Model Layer (`app/models/`)

- SQLAlchemy declarative models define schema, relationships, and simple field-level constraints.
- No HTTP logic, no service calls, no external I/O inside models.

## Cross-Layer Rules

- No cross-layer shortcuts: controllers must not call repositories directly; models must not call services.
- Dependency direction: Controller → Service → Repository → Model.
- Shared utilities go in `app/utils/`; they must not import from any MVC layer.

## Definition Of Done

- Each changed file belongs clearly to one layer and imports only from layers below it.
- No business logic lives outside the service layer.
- No database queries live outside the repository layer.
