---
description: "Enforces strict Test-Driven Development for all Python code changes. Apply when writing, modifying, or reviewing any Python file."
name: "TDD Workflow"
applyTo:
  - "**/*.py"
---
# TDD Workflow Rules

## Red-Green-Refactor Is Mandatory

- Always start by writing a failing test that defines the desired behavior before writing implementation code.
- Implement the smallest code change needed to make the failing test pass.
- Refactor only after tests are green and passing.
- Never write implementation code without a corresponding failing test first.

## Test Requirements For Every Change

- Every requested code change must include new or updated automated tests — no exceptions, including small refactors and non-functional edits.
- Prefer the narrowest useful test level first:
  - Unit tests for business rules in services and domain logic.
  - Integration tests for database behavior and repository boundaries.
  - Route/controller tests for request validation, authorization, and response contracts.
- Bug fixes must include a regression test that fails before the fix and passes after.
- Keep tests deterministic and isolated; avoid real network calls, real file I/O, and real external services in unit tests.
- Tag tests with `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.e2e`.

## Definition Of Done

- Tests are written first and pass after implementation.
- Changed behavior is covered by tests that would fail without the change.
- No untested code paths are introduced for logic that has observable side effects.
