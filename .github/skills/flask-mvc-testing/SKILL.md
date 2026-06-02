---
name: flask-mvc-testing
description: 'E2E test Flask MVC apps with pytest-playwright. Use when: browser tests, auth/login flows, form submissions, redirects, protected pages, page object model, anti-flaky waits, screenshots/traces, CI Playwright execution.'
argument-hint: 'Flask stack details, auth model, target flow (login/CRUD/validation/protected routes), and whether local or CI setup is needed.'
user-invocable: true
---

# Flask MVC E2E Testing With Playwright + pytest

## What This Skill Produces
- A repeatable browser E2E setup for Flask MVC using `pytest` + `pytest-playwright`.
- Live Flask server fixture patterns for local and CI execution.
- Page Object Model (POM) structure with reusable actions/assertions.
- Reliable patterns for login/auth flows, forms, redirects, and protected pages.
- Anti-flaky selector/wait guidance and debugging with screenshots/tracing.
- Ready-to-copy tests for login, CRUD, validation errors, and access control.

## When To Use
- You need confidence in full user journeys across multiple pages.
- Route-level tests already exist, and you want end-to-end browser coverage.
- You must validate real redirects, cookie/session auth, and UI-level validation messages.
- You need stable Playwright tests for CI.

## Use This, Not That
- Use Flask test client for fast server-side logic checks.
- Use Playwright E2E only for cross-page user behavior and browser-rendered outcomes.
- Keep a small, high-value E2E suite; avoid duplicating all integration tests.

---

## 1. Install And Configure pytest-playwright

### Dependencies

```bash
pip install pytest pytest-playwright playwright
python -m playwright install --with-deps chromium
```

### `pytest.ini`

```ini
[pytest]
minversion = 8.0
addopts = -ra --strict-markers
markers =
    e2e: browser end-to-end tests
    auth: login/session/authorization flows
    smoke: quick critical-path checks

testpaths = tests
```

### Suggested test layout

```text
tests/
  conftest.py
  e2e/
    pages/
      base_page.py
      login_page.py
      posts_page.py
    test_login_flow.py
    test_crud_flow.py
    test_validation_errors.py
    test_protected_pages.py
```

---

## 2. Run Flask As A Live Server During Tests

Use an app-factory fixture and start a real HTTP server in a background thread.

```python
# tests/conftest.py
from __future__ import annotations

import socket
import threading
from contextlib import closing
from dataclasses import dataclass

import pytest
from werkzeug.serving import make_server

from app import create_app
from app.extensions import db as _db


TEST_CONFIG = {
    "TESTING": True,
    "WTF_CSRF_ENABLED": False,
    "SECRET_KEY": "test-secret",
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
}


@dataclass
class LiveServer:
    base_url: str


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def app():
    app = create_app(TEST_CONFIG)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    connection = _db.engine.connect()
    transaction = connection.begin()
    _db.session.configure(bind=connection)

    yield _db

    _db.session.remove()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def live_server(app) -> LiveServer:
    port = _free_port()
    host = "127.0.0.1"
    server = make_server(host, port, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield LiveServer(base_url=f"http://{host}:{port}")

    server.shutdown()
    thread.join(timeout=5)
```

Notes:
- Keep `db` at function scope to avoid state leakage.
- Disable CSRF in test config unless explicitly validating CSRF behavior.

---

## 3. Test Data Setup Before Browser Steps

Seed required data before opening pages (users, roles, records). Avoid creating fixtures through UI unless the test explicitly verifies creation UX.

```python
# tests/conftest.py (append)
from app.models import User, Post


@pytest.fixture
def make_user(db):
    def _make_user(email: str, password: str, is_admin: bool = False) -> User:
        user = User(email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return _make_user


@pytest.fixture
def make_post(db):
    def _make_post(title: str, body: str, author_id: int) -> Post:
        post = Post(title=title, body=body, author_id=author_id)
        db.session.add(post)
        db.session.commit()
        return post

    return _make_post
```

---

## 4. Page Object Model (POM)

### Base page

```python
# tests/e2e/pages/base_page.py
class BasePage:
    def __init__(self, page, base_url: str):
        self.page = page
        self.base_url = base_url

    def goto(self, path: str) -> None:
        self.page.goto(f"{self.base_url}{path}")
```

### Login page

```python
# tests/e2e/pages/login_page.py
from .base_page import BasePage


class LoginPage(BasePage):
    email = "[data-testid='login-email']"
    password = "[data-testid='login-password']"
    submit = "[data-testid='login-submit']"
    flash_error = "[data-testid='flash-error']"

    def open(self) -> None:
        self.goto("/auth/login")

    def login(self, email: str, password: str) -> None:
        self.page.locator(self.email).fill(email)
        self.page.locator(self.password).fill(password)
        self.page.locator(self.submit).click()
```

### Posts page

```python
# tests/e2e/pages/posts_page.py
from .base_page import BasePage


class PostsPage(BasePage):
    title = "[data-testid='post-title']"
    body = "[data-testid='post-body']"
    save = "[data-testid='post-save']"
    rows = "[data-testid='post-row']"

    def open_new(self) -> None:
        self.goto("/posts/new")

    def create(self, title: str, body: str) -> None:
        self.page.locator(self.title).fill(title)
        self.page.locator(self.body).fill(body)
        self.page.locator(self.save).click()
```

POM rules:
- Keep selectors in page classes, not test files.
- Expose user intent methods (`login`, `create`, `delete`) over low-level clicks.
- Put assertions mostly in tests; keep pages action-focused.

---

## 5. Selector Strategy (Anti-Flaky)

Priority order:
1. `get_by_test_id` / `[data-testid='...']`
2. semantic role + name (`get_by_role("button", name="Save")`)
3. visible text (`get_by_text`) only for stable copy
4. avoid CSS chains tied to layout (`.card > div:nth-child(2) > ...`)

Example helper:

```python
# tests/e2e/selectors.py
def by_test_id(test_id: str) -> str:
    return f"[data-testid='{test_id}']"
```

---

## 6. Waiting Strategy (Anti-Flaky)

Rules:
- Wait for user-visible outcomes, not arbitrary time.
- Never use `page.wait_for_timeout(...)` in committed tests.
- Prefer Playwright auto-wait with `expect(...)` assertions.
- After click/submit causing navigation, assert URL and heading/flash.

Examples:

```python
from playwright.sync_api import expect

# URL transition
expect(page).to_have_url(r".*/dashboard$")

# UI outcome transition
expect(page.get_by_test_id("flash-success")).to_contain_text("Created")

# Table eventually updated
expect(page.locator("[data-testid='post-row']")).to_have_count(1)
```

---

## 7. Auth, Navigation, Redirect Flows

### Login success + redirect

```python
# tests/e2e/test_login_flow.py
import pytest
from playwright.sync_api import expect

from tests.e2e.pages.login_page import LoginPage


@pytest.mark.e2e
@pytest.mark.auth
def test_login_success_redirects_to_dashboard(page, live_server, make_user):
    make_user(email="alice@example.com", password="correct-password")

    login = LoginPage(page, live_server.base_url)
    login.open()
    login.login("alice@example.com", "correct-password")

    expect(page).to_have_url(r".*/dashboard$")
    expect(page.get_by_test_id("dashboard-title")).to_contain_text("Dashboard")
```

### Login failure

```python
@pytest.mark.e2e
@pytest.mark.auth
def test_login_failure_shows_error(page, live_server, make_user):
    make_user(email="alice@example.com", password="correct-password")

    login = LoginPage(page, live_server.base_url)
    login.open()
    login.login("alice@example.com", "wrong-password")

    expect(page).to_have_url(r".*/auth/login$")
    expect(page.get_by_test_id("flash-error")).to_contain_text("Invalid credentials")
```

---

## 8. Form Submission And Validation Errors

```python
# tests/e2e/test_validation_errors.py
import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_registration_validation_errors(page, live_server):
    page.goto(f"{live_server.base_url}/auth/register")

    page.get_by_test_id("register-email").fill("not-an-email")
    page.get_by_test_id("register-password").fill("123")
    page.get_by_test_id("register-confirm").fill("456")
    page.get_by_test_id("register-submit").click()

    expect(page).to_have_url(r".*/auth/register$")
    expect(page.get_by_test_id("error-email")).to_contain_text("valid email")
    expect(page.get_by_test_id("error-password")).to_contain_text("at least")
    expect(page.get_by_test_id("error-confirm")).to_contain_text("must match")
```

---

## 9. CRUD Flow Example

```python
# tests/e2e/test_crud_flow.py
import pytest
from playwright.sync_api import expect

from tests.e2e.pages.login_page import LoginPage
from tests.e2e.pages.posts_page import PostsPage


@pytest.mark.e2e
def test_create_edit_delete_post(page, live_server, make_user):
    make_user("editor@example.com", "secret")

    login = LoginPage(page, live_server.base_url)
    posts = PostsPage(page, live_server.base_url)

    login.open()
    login.login("editor@example.com", "secret")

    posts.open_new()
    posts.create("First title", "Initial body")

    expect(page.get_by_test_id("flash-success")).to_contain_text("created")
    expect(page.get_by_test_id("post-row")).to_contain_text("First title")

    page.get_by_test_id("post-edit").first.click()
    page.get_by_test_id("post-title").fill("Updated title")
    page.get_by_test_id("post-save").click()
    expect(page.get_by_test_id("post-row")).to_contain_text("Updated title")

    page.get_by_test_id("post-delete").first.click()
    expect(page.get_by_test_id("post-row")).to_have_count(0)
```

---

## 10. Protected Page Example

```python
# tests/e2e/test_protected_pages.py
import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
@pytest.mark.auth
def test_protected_page_redirects_anonymous_user(page, live_server):
    page.goto(f"{live_server.base_url}/dashboard")

    expect(page).to_have_url(r".*/auth/login\?next=/dashboard")
    expect(page.get_by_test_id("login-submit")).to_be_visible()
```

---

## 11. Screenshots, Tracing, And Debugging

Capture artifacts only on failures (or on demand in CI).

```python
# tests/conftest.py (append)
import os
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def trace_on_failure(page, request):
    artifacts = Path("test-artifacts")
    artifacts.mkdir(exist_ok=True)

    trace_file = artifacts / f"{request.node.name}-trace.zip"
    screenshot_file = artifacts / f"{request.node.name}.png"

    page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if failed:
        page.screenshot(path=str(screenshot_file), full_page=True)
        page.context.tracing.stop(path=str(trace_file))
    else:
        page.context.tracing.stop()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
```

Useful local debug flags:

```bash
pytest -m e2e --headed -k login -x
pytest -m e2e --headed --slowmo 200
pytest -m e2e --browser chromium
```

---

## 12. Anti-Flaky Rules (Required)

- Seed all prerequisite data in fixtures before browser navigation.
- Do not share mutable DB/browser state across tests.
- One user journey per test; avoid mega-tests.
- Assert URL and page state after each major action.
- Use deterministic selectors (`data-testid`) for all critical controls.
- Keep retries as a last resort; fix waits/selectors first.
- Run E2E serially if app state cannot be isolated; otherwise parallelize safely.

Optional flaky triage config:

```ini
# pytest.ini
addopts = -ra --strict-markers --maxfail=1
```

---

## 13. CI Execution Guidance

### GitHub Actions example

```yaml
name: e2e
on: [push, pull_request]

jobs:
  playwright-e2e:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-playwright playwright

      - name: Install browser
        run: python -m playwright install --with-deps chromium

      - name: Run e2e tests
        run: pytest -m e2e --browser chromium

      - name: Upload artifacts
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-artifacts
          path: test-artifacts/
```

CI tips:
- Pin Python and browser channel for reproducibility.
- Upload screenshots/traces on failure.
- Keep smoke E2E tests small for fast PR feedback.

---

## 14. Completion Checklist

- [ ] `pytest-playwright` installed and browser binaries provisioned.
- [ ] Live Flask server fixture serves app on ephemeral port.
- [ ] DB/data fixtures seed required users/records pre-navigation.
- [ ] POM classes encapsulate selectors and user actions.
- [ ] Selectors use `data-testid` for all critical interactions.
- [ ] Waits use URL/DOM assertions, not sleep/timeouts.
- [ ] Login/auth, CRUD, validation, and protected-route E2E tests pass.
- [ ] Failure artifacts (screenshots + trace) are captured.
- [ ] CI executes `pytest -m e2e` and uploads artifacts on failure.

## Quick Command Reference

```bash
pytest -m e2e
pytest -m "e2e and auth"
pytest tests/e2e/test_login_flow.py -x --headed
```
