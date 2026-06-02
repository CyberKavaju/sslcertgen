---
name: python-mocking-external-dependencies
description: 'Mock external dependencies in Python tests with unittest.mock, pytest monkeypatch, responses (requests), and respx (httpx). Use when testing Flask service-layer code, retries, timeouts, failures, environment variables, and integration boundaries without over-mocking.'
argument-hint: 'What dependency type are you mocking (repo/service/env/http) and what behavior should be simulated?'
user-invocable: true
disable-model-invocation: false
---

# Python Mocking External Dependencies Playbook

## Outcome
Create reliable, behavior-focused tests for Python code that depends on repositories, external services, environment variables, and HTTP APIs.

## When To Use
- Tests are slow or flaky because they call real databases, APIs, queues, or file/network resources.
- You need deterministic coverage of failures (timeouts, retries, malformed responses, non-2xx status codes).
- You are testing Flask service-layer orchestration and domain rules.

## Scope And Boundaries
- Prefer mocking at I/O boundaries (DB adapters, HTTP clients, SDK wrappers, system env).
- Keep core domain logic real whenever possible.
- Use fakes or factories for rich domain objects; avoid replacing everything with mocks.

## Tool Selection Matrix

### `pytest` `monkeypatch`
Use when you need temporary runtime mutation:
- Environment variables (`os.environ`)
- Module-level constants
- Replacing attributes/functions without decorator nesting

### `unittest.mock.patch`
Use when you need:
- Call assertions (`assert_called_once_with`, `assert_has_calls`)
- Autospecced mocks (`autospec=True`) to catch bad signatures
- Scoped patching with decorators/context managers

### `responses` (for `requests`)
Use when code calls `requests.*` and you want declarative HTTP stubs.

### `respx` (for `httpx`)
Use when code calls `httpx.Client` / `httpx.AsyncClient` and you need route-level assertions.

## Golden Rules
1. Patch where the symbol is looked up, not where it is defined.
2. Use `autospec=True` (or `spec_set`) for safer mocks.
3. Assert behavior and outcomes first; interaction assertions second.
4. One test should verify one business behavior with one dominant failure mode.
5. Over-mocking is a smell: if a test mocks every collaborator, redesign seams or use fakes.

## Step-By-Step Workflow

### 1. Identify the boundary and test level
- Service-layer unit test: mock repositories, external API clients, and side-effect adapters.
- Integration test: keep real DB/session but mock outbound HTTP.
- End-to-end test: avoid mocks except truly external systems.

Completion check:
- Test remains fast (<100ms typical unit test), deterministic, and isolated.

### 2. Pick mocking strategy by dependency type
- Repository or collaborator object: `Mock(spec=RepoClass)` or `create_autospec`.
- Environment variable: `monkeypatch.setenv` / `monkeypatch.delenv`.
- `requests` API: `responses`.
- `httpx` API: `respx`.

Completion check:
- You can express the scenario with minimal patch surface.

### 3. Arrange realistic inputs and return shapes
- Mirror real payload schemas and repository DTO/entity contracts.
- Include negative shapes for error handling branches.

Completion check:
- Test data could plausibly come from production.

### 4. Execute and assert
- Assert returned value/state transitions first.
- Assert critical interactions only (e.g., retry count, save called once, proper timeout parameter).

Completion check:
- Failure message clearly explains business regression.

### 5. Add resilience-path cases
- Timeout
- Retry eventually succeeds
- Retry exhausted
- Upstream bad JSON / missing fields
- Non-2xx / 5xx response mapping

Completion check:
- Each resilience policy has at least one explicit test.

## Branching Guidance
- If mocking requires 4+ patches in one test, introduce a wrapper interface/facade and mock that instead.
- If you are asserting many internal calls, shift assertions to externally visible outcomes.
- If retry logic uses sleep, patch the sleeper function (for example `time.sleep`) to avoid slow tests.

## Flask Service-Layer Examples

### Example Service Under Test
```python
# app/services/orders.py
from dataclasses import dataclass
import requests


class UpstreamUnavailable(Exception):
    pass


@dataclass
class OrderService:
    order_repo: object
    payment_client: object
    max_retries: int = 3

    def create_order(self, user_id: int, sku: str, qty: int) -> dict:
        if qty <= 0:
            raise ValueError("qty must be positive")

        order = self.order_repo.create(user_id=user_id, sku=sku, qty=qty)

        for attempt in range(1, self.max_retries + 1):
            try:
                auth = self.payment_client.authorize(order_id=order["id"], amount=order["total"])
                self.order_repo.mark_authorized(order["id"], auth_id=auth["id"])
                return {"order_id": order["id"], "status": "authorized"}
            except TimeoutError:
                if attempt == self.max_retries:
                    self.order_repo.mark_failed(order["id"], reason="payment_timeout")
                    raise UpstreamUnavailable("payment timeout")

    def shipping_quote(self, postal_code: str) -> float:
        r = requests.get(
            "https://ship.example/quote",
            params={"postal_code": postal_code},
            timeout=2.0,
        )
        r.raise_for_status()
        body = r.json()
        if "amount" not in body:
            raise ValueError("bad response: amount missing")
        return float(body["amount"])
```

### Example: Repository + Service Collaborator Mocking
```python
# tests/services/test_orders_service.py
from unittest.mock import create_autospec
import pytest

from app.services.orders import OrderService, UpstreamUnavailable


class OrderRepo:
    def create(self, user_id: int, sku: str, qty: int) -> dict: ...
    def mark_authorized(self, order_id: int, auth_id: str) -> None: ...
    def mark_failed(self, order_id: int, reason: str) -> None: ...


class PaymentClient:
    def authorize(self, order_id: int, amount: int) -> dict: ...


def test_create_order_authorized_happy_path():
    repo = create_autospec(OrderRepo, spec_set=True)
    payment = create_autospec(PaymentClient, spec_set=True)

    repo.create.return_value = {"id": 10, "total": 2500}
    payment.authorize.return_value = {"id": "auth_123"}

    svc = OrderService(order_repo=repo, payment_client=payment)
    result = svc.create_order(user_id=7, sku="ABC", qty=2)

    assert result == {"order_id": 10, "status": "authorized"}
    repo.create.assert_called_once_with(user_id=7, sku="ABC", qty=2)
    payment.authorize.assert_called_once_with(order_id=10, amount=2500)
    repo.mark_authorized.assert_called_once_with(10, auth_id="auth_123")


def test_create_order_retries_then_fails():
    repo = create_autospec(OrderRepo, spec_set=True)
    payment = create_autospec(PaymentClient, spec_set=True)

    repo.create.return_value = {"id": 11, "total": 1200}
    payment.authorize.side_effect = TimeoutError("upstream timeout")

    svc = OrderService(order_repo=repo, payment_client=payment, max_retries=3)

    with pytest.raises(UpstreamUnavailable):
        svc.create_order(user_id=1, sku="XYZ", qty=1)

    assert payment.authorize.call_count == 3
    repo.mark_failed.assert_called_once_with(11, reason="payment_timeout")
```

### Example: `monkeypatch` for Environment Variables
```python
# app/config.py
import os


def payment_base_url() -> str:
    return os.environ.get("PAYMENT_BASE_URL", "https://default-payments.local")
```

```python
# tests/test_config.py
from app.config import payment_base_url


def test_payment_base_url_from_env(monkeypatch):
    monkeypatch.setenv("PAYMENT_BASE_URL", "https://payments.test")
    assert payment_base_url() == "https://payments.test"


def test_payment_base_url_default(monkeypatch):
    monkeypatch.delenv("PAYMENT_BASE_URL", raising=False)
    assert payment_base_url() == "https://default-payments.local"
```

### Example: `mock.patch` for Lookup-Location Correctness
```python
# app/services/notify.py
from app.integrations.email import send_email


def send_welcome(user_email: str) -> None:
    send_email(to=user_email, subject="Welcome", body="Hello!")
```

```python
# tests/services/test_notify.py
from unittest.mock import patch

from app.services.notify import send_welcome


@patch("app.services.notify.send_email", autospec=True)
def test_send_welcome_calls_email(mock_send_email):
    send_welcome("u@example.com")
    mock_send_email.assert_called_once_with(
        to="u@example.com", subject="Welcome", body="Hello!"
    )
```

### Example: Mocking External HTTP with `responses` (`requests`)
```python
import responses

from app.services.orders import OrderService


@responses.activate
def test_shipping_quote_success_with_responses(order_service: OrderService):
    responses.get(
        "https://ship.example/quote",
        json={"amount": "12.50"},
        status=200,
    )

    amount = order_service.shipping_quote("94016")

    assert amount == 12.50
```

```python
import pytest
import responses

from app.services.orders import OrderService


@responses.activate
def test_shipping_quote_bad_payload(order_service: OrderService):
    responses.get("https://ship.example/quote", json={"unexpected": 1}, status=200)

    with pytest.raises(ValueError, match="amount missing"):
        order_service.shipping_quote("94016")
```

### Example: Mocking External HTTP with `respx` (`httpx`)
```python
# app/integrations/inventory.py
import httpx


class InventoryClient:
    def __init__(self, base_url: str):
        self._base_url = base_url

    def in_stock(self, sku: str) -> bool:
        with httpx.Client(base_url=self._base_url, timeout=1.0) as client:
            r = client.get(f"/inventory/{sku}")
            r.raise_for_status()
            return bool(r.json()["in_stock"])
```

```python
import httpx
import respx

from app.integrations.inventory import InventoryClient


@respx.mock
def test_inventory_in_stock():
    route = respx.get("https://inventory.test/inventory/ABC").mock(
        return_value=httpx.Response(200, json={"in_stock": True})
    )

    client = InventoryClient(base_url="https://inventory.test")
    assert client.in_stock("ABC") is True
    assert route.called
```

### Example: Retry Then Success
```python
from unittest.mock import create_autospec

from app.services.orders import OrderService


class OrderRepo:
    def create(self, user_id: int, sku: str, qty: int) -> dict: ...
    def mark_authorized(self, order_id: int, auth_id: str) -> None: ...


class PaymentClient:
    def authorize(self, order_id: int, amount: int) -> dict: ...


def test_retry_then_success_marks_authorized_once():
    repo = create_autospec(OrderRepo, spec_set=True)
    payment = create_autospec(PaymentClient, spec_set=True)

    repo.create.return_value = {"id": 21, "total": 990}
    payment.authorize.side_effect = [TimeoutError(), {"id": "auth_late"}]

    svc = OrderService(order_repo=repo, payment_client=payment, max_retries=3)
    result = svc.create_order(user_id=2, sku="SKU-1", qty=1)

    assert result["status"] == "authorized"
    assert payment.authorize.call_count == 2
    repo.mark_authorized.assert_called_once_with(21, auth_id="auth_late")
```

## Best Practices Checklist
- Use `autospec` or `spec_set` for collaborator mocks.
- Prefer constructor injection for easier mocking.
- Keep patch lifetime narrow (context manager, fixture, decorator).
- Test both success and at least one realistic failure per external boundary.
- Assert meaningful side effects (state changes, persisted status).
- Avoid asserting non-essential internal calls.

## Anti-Patterns To Avoid
- Mocking private methods of the unit under test.
- Mocking standard library primitives unnecessarily.
- Asserting every single call argument for every collaborator.
- Returning impossible payloads that hide real parsing bugs.
- Using network in unit tests.

## Recommended Pytest Fixtures
```python
import pytest
from unittest.mock import create_autospec

from app.services.orders import OrderService


class OrderRepo:
    def create(self, user_id: int, sku: str, qty: int) -> dict: ...
    def mark_authorized(self, order_id: int, auth_id: str) -> None: ...
    def mark_failed(self, order_id: int, reason: str) -> None: ...


class PaymentClient:
    def authorize(self, order_id: int, amount: int) -> dict: ...


@pytest.fixture
def repo_mock():
    return create_autospec(OrderRepo, spec_set=True)


@pytest.fixture
def payment_mock():
    return create_autospec(PaymentClient, spec_set=True)


@pytest.fixture
def order_service(repo_mock, payment_mock):
    return OrderService(order_repo=repo_mock, payment_client=payment_mock)
```

## Definition Of Done
- Tests are deterministic and isolated from network/database side effects.
- Each mocked boundary maps to a clear contract.
- Retry/timeout/error branches are explicitly covered.
- Test intent is readable without digging through mock internals.
