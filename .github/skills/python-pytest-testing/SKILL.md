---
name: python-pytest-testing
description: 'Build and maintain reliable Python test suites with pytest. Use when setting up pytest, designing test structure, writing fixtures, parametrizing cases, using markers, monkeypatch, temporary files, and enforcing AAA with strong test isolation for Flask MVC or any Python project.'
argument-hint: 'Project type (Flask MVC/library/service), test focus (unit/integration/e2e), and constraints (CI time, coverage target).'
user-invocable: true
---

# Python Pytest Testing

## What This Skill Produces
- A consistent pytest setup and test layout for Python projects.
- Fast, isolated tests using fixtures, monkeypatch, tmp_path, and markers.
- Readable tests that follow Arrange, Act, Assert (AAA).
- Reusable patterns for Flask MVC projects that also work in non-Flask codebases.

## When To Use
- You are introducing pytest to a project.
- Tests are flaky or tightly coupled to environment/state.
- You need clear conventions for naming, fixtures, and folder layout.
- You want examples for service, repository, and pure function testing.

## Procedure

### 1. Install and Configure Pytest
Use a minimal starting configuration, then add plugins only when needed.

```bash
python -m pip install -U pytest
```

Optional but common additions:

```bash
python -m pip install -U pytest-cov pytest-mock
```

Create `pytest.ini`:

```ini
[pytest]
minversion = 8.0
addopts = -ra
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
testpaths = tests
markers =
    unit: fast isolated tests
    integration: tests crossing process, DB, or network boundaries
    slow: long-running tests
```

For Flask MVC projects, keep app creation importable via an app factory (for example, `create_app`) so tests can instantiate isolated app instances.

### 2. Adopt a Predictable Folder Structure
Keep tests parallel to architectural boundaries.

```text
project/
  src/
    app/
      services/
      repositories/
      domain/
      web/
  tests/
    conftest.py
    unit/
      services/
      repositories/
      domain/
    integration/
      web/
      repositories/
```

Guidance:
- Place shared fixtures in `tests/conftest.py`.
- Keep feature-local fixtures near related tests when scope is narrow.
- Avoid a single giant fixture file for all test concerns.

### 3. Use Naming Conventions That Explain Behavior
- File names: `test_<module>.py`.
- Test function names: `test_<expected_behavior>_<condition>()`.
- Test classes are optional; prefer plain functions unless grouping improves readability.

Examples:
- `test_create_order_rejects_invalid_currency`
- `test_find_user_returns_none_when_missing`

### 4. Write Tests with AAA
Each test should have one clear behavior target.

```python
def test_discount_applied_for_premium_customer():
    # Arrange
    customer_tier = "premium"
    subtotal = 120

    # Act
    total = apply_discount(subtotal, customer_tier)

    # Assert
    assert total == 108
```

Checklist:
- Arrange is explicit and minimal.
- Act executes exactly what is under test.
- Assert checks behavior, not implementation details.

### 5. Build Fixture Strategy Intentionally
Prefer narrow scope by default.

```python
# tests/conftest.py
import pytest

@pytest.fixture
def settings():
    return {"tax_rate": 0.2, "currency": "USD"}

@pytest.fixture
def order_service(settings):
    return OrderService(settings=settings)
```

Fixture guidance:
- Use `function` scope unless expensive setup justifies broader scope.
- Keep fixtures deterministic and side-effect free.
- Use factory fixtures for varied input objects.

### 6. Use Parametrization for Input Matrices
Replace repetitive tests with parameter sets.

```python
import pytest

@pytest.mark.parametrize(
    "value,expected",
    [
        ("", False),
        ("abc", True),
        ("  ", False),
    ],
)
def test_is_valid_name(value, expected):
    assert is_valid_name(value) is expected
```

Tips:
- Use `ids=` for readability in failing cases.
- Keep each parameter row focused on one reason to fail or pass.

### 7. Use Markers to Control Test Selection
Standardize marker semantics and enforce them in code review.

```python
import pytest

@pytest.mark.unit
def test_slugify_handles_unicode_letters():
    assert slugify("Cafe") == "cafe"

@pytest.mark.integration
@pytest.mark.slow
def test_repository_reads_from_real_db(db_session):
    ...
```

Run subsets:

```bash
pytest -m unit
pytest -m "integration and not slow"
```

### 8. Use Monkeypatch for Process Boundary Isolation
Mock external dependencies at integration boundaries, not internal implementation details.

```python
def test_send_receipt_uses_mailer(monkeypatch):
    calls = []

    def fake_send(to, subject, body):
        calls.append((to, subject, body))

    monkeypatch.setattr("app.services.mailer.send", fake_send)

    send_receipt("user@example.com", "Order #42")

    assert len(calls) == 1
    assert calls[0][0] == "user@example.com"
```

Prefer dependency injection when possible; use monkeypatch when refactoring is not practical.

### 9. Use Temporary Files and Directories Safely
Never write test artifacts into project root.

```python
def test_export_report_writes_json(tmp_path):
    out_file = tmp_path / "report.json"

    export_report({"status": "ok"}, out_file)

    assert out_file.exists()
    assert out_file.read_text() == '{"status": "ok"}'
```

Use `tmp_path_factory` for expensive shared temp setup.

### 10. Enforce Test Isolation
Isolation rules:
- No shared mutable global state between tests.
- No hidden ordering dependencies.
- No network/DB/file usage in unit tests unless explicitly mocked.
- Reset environment variables and time/randomness sources when patched.

Isolation techniques:
- `monkeypatch.setenv` / `monkeypatch.delenv`
- fixture teardown via `yield`
- ephemeral resources via `tmp_path`

## Example Patterns

### Service Example (Business Logic)

```python
# src/app/services/pricing.py
class PricingService:
    def __init__(self, tax_rate: float):
        self.tax_rate = tax_rate

    def total(self, subtotal: float) -> float:
        return round(subtotal * (1 + self.tax_rate), 2)
```

```python
# tests/unit/services/test_pricing_service.py
from app.services.pricing import PricingService


def test_total_applies_tax_rate():
    # Arrange
    svc = PricingService(tax_rate=0.2)

    # Act
    result = svc.total(100)

    # Assert
    assert result == 120.0
```

### Repository Example (Persistence Boundary)

```python
# src/app/repositories/user_repository.py
class UserRepository:
    def __init__(self, session):
        self.session = session

    def find_by_email(self, email: str):
        return self.session.query_user_by_email(email)
```

```python
# tests/unit/repositories/test_user_repository.py
from app.repositories.user_repository import UserRepository


class FakeSession:
    def __init__(self, users):
        self.users = users

    def query_user_by_email(self, email):
        return self.users.get(email)


def test_find_by_email_returns_user_when_present():
    # Arrange
    repo = UserRepository(session=FakeSession({"a@x.com": {"id": 1}}))

    # Act
    user = repo.find_by_email("a@x.com")

    # Assert
    assert user == {"id": 1}
```

### Pure Function Example

```python
# src/app/domain/math_utils.py
def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))
```

```python
# tests/unit/domain/test_math_utils.py
import pytest
from app.domain.math_utils import clamp


@pytest.mark.parametrize(
    "value,low,high,expected",
    [
        (-1, 0, 10, 0),
        (5, 0, 10, 5),
        (99, 0, 10, 10),
    ],
)
def test_clamp_bounds_values(value, low, high, expected):
    # Act
    result = clamp(value, low, high)

    # Assert
    assert result == expected
```

## Flask MVC Notes (Still Generic)
- Prefer app factory fixtures that create a new Flask app per test function or module.
- Use a separate test config class (`TESTING=True`, isolated DB URL, disabled external integrations).
- Test controllers/views through Flask test client in integration tests.
- Keep service/domain unit tests Flask-independent when possible.

## Common Anti-Patterns
- Asserting internal calls rather than observable behavior.
- Overusing `autouse` fixtures that hide setup and increase coupling.
- Mixing unit and integration concerns in one test.
- Relying on shared databases/files without cleanup.
- Large tests with multiple Act steps and many unrelated assertions.
- Non-deterministic tests tied to wall clock, randomness, or environment leakage.

## Completion Checks
- Pytest runs with explicit marker definitions and no unknown marker warnings.
- Unit tests pass offline and in parallel-friendly execution.
- New tests follow AAA and naming conventions.
- Integration tests are explicitly marked and slower paths are separable.
- Flaky tests are either fixed with isolation or quarantined with a clear owner and follow-up plan.
