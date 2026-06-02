---
name: flask-ci-testing
description: 'CI pipeline for Python Flask MVC projects. Use when: setting up GitHub Actions, running pytest in CI, enforcing coverage thresholds, running Ruff linting, running mypy/pyright type checks, running Playwright E2E in CI, installing browser dependencies, configuring test matrix, injecting environment variables and secrets, provisioning a database in CI, uploading Playwright traces and screenshots, deciding between tox and nox.'
argument-hint: 'Flask project details: database engine (SQLite/PostgreSQL/MySQL), coverage target (e.g. 80%), Playwright browser (chromium/firefox/webkit), Python versions to test, and any required secrets.'
user-invocable: true
---

# Flask CI Testing — GitHub Actions Guide

## What This Skill Produces
- A complete, copy-ready **GitHub Actions** workflow for a Python Flask MVC project.
- Parallel jobs for lint/type-check, unit+integration tests, and Playwright E2E tests.
- Coverage enforcement with `pytest-cov` and a configurable fail threshold.
- Ruff for fast linting and formatting checks.
- `mypy` or `pyright` for static type analysis.
- Playwright browser install with dependency caching.
- Artifact upload for Playwright traces and screenshots on failure.
- Database provisioning (PostgreSQL service container or SQLite).
- Guidance on when to use `tox` or `nox` instead of raw Actions steps.

## When To Use
- You are wiring up a new CI pipeline for a Flask project.
- Tests pass locally but you need them running on every push/PR.
- You want coverage gates, type checks, and lint enforced in the same pipeline.
- You need Playwright E2E tests that run in a headless browser inside CI.
- You are deciding between a single workflow file and `tox`/`nox`.

---

## 1. Dependency and Caching Strategy

### `requirements` layout
Split requirements to cache layers independently:

```
requirements/
  base.txt        # runtime deps
  dev.txt         # -r base.txt + pytest, coverage, ruff, mypy, playwright…
  ci.txt          # optional: CI-only extras (e.g. pytest-github-actions-annotate-failures)
```

### pip caching in Actions
Use `actions/cache` keyed on the hash of your requirements files so the layer is invalidated only when deps change:

```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements/**') }}
    restore-keys: ${{ runner.os }}-pip-
```

### Playwright browser cache
Playwright downloads browser binaries to a platform-specific cache directory. Key the cache on the Playwright version so browsers are re-downloaded only on upgrades:

```yaml
- name: Cache Playwright browsers
  uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: playwright-${{ runner.os }}-${{ hashFiles('requirements/dev.txt') }}
```

---

## 2. Environment Variables and Secrets

### Variables vs Secrets
| Concern | Use |
|---------|-----|
| Non-sensitive config (`FLASK_ENV`, `DATABASE_URL`) | `env:` block at job or step level |
| Sensitive values (API keys, `SECRET_KEY`) | GitHub Actions **Secrets** via `${{ secrets.NAME }}` |
| Values shared across jobs | Repository or environment-level variables/secrets |

### Inject at job level (preferred)
```yaml
jobs:
  test:
    env:
      FLASK_ENV: testing
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
      SECRET_KEY: ${{ secrets.SECRET_KEY }}
```

Avoid injecting secrets at the workflow level — it widens their exposure.

### `.env.ci` file pattern
Some projects source a checked-in `.env.ci` with non-secret values and override secrets at run time:

```yaml
- name: Load CI env
  run: cp .env.ci .env

- name: Override secrets
  run: echo "SECRET_KEY=${{ secrets.SECRET_KEY }}" >> .env
```

---

## 3. Database Setup in CI

### Option A — PostgreSQL service container (recommended for parity)

```yaml
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: testdb
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

Run migrations before tests:
```yaml
- name: Run migrations
  run: flask db upgrade
  env:
    FLASK_APP: app:create_app
```

### Option B — SQLite (fast, zero-config)
Override `DATABASE_URL` to an in-memory or file-based SQLite URI. Suitable for unit/integration tests that do not require Postgres-specific behavior:

```yaml
env:
  DATABASE_URL: sqlite:///test.db
```

### Option C — MySQL service container
```yaml
services:
  mysql:
    image: mysql:8
    env:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: testdb
    ports:
      - 3306:3306
    options: >-
      --health-cmd "mysqladmin ping -h 127.0.0.1"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

---

## 4. Ruff — Lint and Format Check

```yaml
- name: Ruff lint
  run: ruff check .

- name: Ruff format check
  run: ruff format --check .
```

`pyproject.toml` baseline config:
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]
ignore = ["E501"]
```

---

## 5. mypy or pyright

### mypy
```yaml
- name: Type check (mypy)
  run: mypy src/
```

`pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.12"
strict = false
ignore_missing_imports = true
```

Start with `ignore_missing_imports = true` to avoid noise from untyped third-party packages. Enable `strict` incrementally per module.

### pyright (alternative)
```yaml
- name: Type check (pyright)
  run: pyright
```

`pyproject.toml`:
```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "basic"
```

**When to choose**: `mypy` has broader Flask/SQLAlchemy plugin ecosystem. `pyright` is faster and works well with VS Code Pylance. For new projects, prefer `pyright`; for legacy projects with existing `mypy` config, stay on `mypy`.

---

## 6. pytest, Coverage, and Markers

### Run unit + integration tests with coverage
```yaml
- name: Run tests
  run: |
    pytest tests/ \
      --ignore=tests/e2e \
      --cov=src \
      --cov-report=term-missing \
      --cov-report=xml \
      --cov-fail-under=80 \
      -v
```

### Upload coverage to Codecov (optional)
```yaml
- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
    fail_ci_if_error: false
```

### `pytest.ini` markers
```ini
[pytest]
markers =
    unit: fast isolated tests
    integration: crosses DB or service boundaries
    e2e: browser end-to-end tests (playwright)
    slow: long-running; excluded from default run
```

---

## 7. Playwright E2E in CI

### Install browser and system dependencies
```yaml
- name: Install Playwright browsers
  run: python -m playwright install --with-deps chromium
```

`--with-deps` installs OS-level system libraries (libnss, libatk, etc.) required for headless Chromium. This is required on GitHub-hosted runners (Ubuntu).

### Run E2E tests
```yaml
- name: Run E2E tests
  run: pytest tests/e2e/ -m e2e --tracing=retain-on-failure --screenshot=only-on-failure -v
  env:
    BASE_URL: http://localhost:5000
```

### Upload traces and screenshots on failure
```yaml
- name: Upload Playwright artifacts
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: playwright-artifacts-${{ matrix.python-version }}
    path: |
      test-results/
      playwright-traces/
    retention-days: 7
```

Configure `pytest-playwright` output dirs in `pytest.ini`:
```ini
[pytest]
playwright_base_url = http://localhost:5000
```

Or via `conftest.py`:
```python
# tests/e2e/conftest.py
import pytest

@pytest.fixture(scope="session")
def base_url():
    return "http://localhost:5000"
```

---

## 8. Test Matrix Strategy

Use a matrix to validate across Python versions (and optionally OS):

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
    # os: [ubuntu-latest, macos-latest]  # add only if cross-OS is needed
```

**Tips:**
- Set `fail-fast: false` so a failure on one Python version doesn't cancel all others.
- Pin the "canonical" version (usually the latest stable) for artifact uploads and coverage reporting to avoid duplicate uploads.
- Add `os` to the matrix only if your app has platform-specific behavior — it quadruples run time.

---

## 9. tox vs nox

| | tox | nox |
|---|---|---|
| Config format | `tox.ini` / `pyproject.toml` | Python (`noxfile.py`) |
| Learning curve | Low (INI familiar) | Low-medium (Python) |
| Flexibility | Medium (plugins) | High (full Python logic) |
| CI integration | Native (`tox -e ci`) | Native (`nox -s test`) |
| Virtualenv management | Built-in | Built-in |
| Best for | Stable multi-env matrix, library publishing | Dynamic sessions, conditional logic, monorepos |

### When to use tox
- You already have a `tox.ini` and need to run the same matrix locally and in CI.
- You are maintaining a library that must support multiple Python/Django/Flask versions.
- You want a dead-simple `tox -e lint,test` convention with minimal setup.

### When to use nox
- Your session logic is conditional (e.g., run mypy only on Python 3.12+).
- You need to share logic between sessions (DRY across lint, test, docs).
- You prefer Python over INI for maintainability.

### Calling tox/nox from Actions
```yaml
# tox
- run: pip install tox tox-gh-actions
- run: tox

# nox
- run: pip install nox
- run: nox -s lint test
```

`tox-gh-actions` automatically maps the `python-version` matrix value to the correct tox environment, so no manual environment mapping is needed.

---

## 10. Complete GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # ── Job 1: Lint and type check ──────────────────────────────────────────────
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements/**') }}
          restore-keys: ${{ runner.os }}-pip-

      - name: Install dev dependencies
        run: pip install -r requirements/dev.txt

      - name: Ruff lint
        run: ruff check .

      - name: Ruff format check
        run: ruff format --check .

      - name: Type check (mypy)
        run: mypy src/

  # ── Job 2: Unit + Integration tests (matrix) ────────────────────────────────
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    needs: lint

    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      FLASK_ENV: testing
      FLASK_APP: app:create_app
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
      SECRET_KEY: ${{ secrets.SECRET_KEY }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('requirements/**') }}
          restore-keys: ${{ runner.os }}-pip-${{ matrix.python-version }}-

      - name: Install dependencies
        run: pip install -r requirements/dev.txt

      - name: Run migrations
        run: flask db upgrade

      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --ignore=tests/e2e \
            --cov=src \
            --cov-report=term-missing \
            --cov-report=xml \
            --cov-fail-under=80 \
            -v

      - name: Upload coverage (canonical version only)
        if: matrix.python-version == '3.12'
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  # ── Job 3: Playwright E2E tests ─────────────────────────────────────────────
  e2e:
    name: Playwright E2E
    runs-on: ubuntu-latest
    needs: test

    env:
      FLASK_ENV: testing
      FLASK_APP: app:create_app
      DATABASE_URL: sqlite:///e2e_test.db
      SECRET_KEY: ${{ secrets.SECRET_KEY }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-e2e-${{ hashFiles('requirements/**') }}
          restore-keys: ${{ runner.os }}-pip-e2e-

      - name: Install dependencies
        run: pip install -r requirements/dev.txt

      - name: Cache Playwright browsers
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-${{ runner.os }}-${{ hashFiles('requirements/dev.txt') }}

      - name: Install Playwright browsers
        run: python -m playwright install --with-deps chromium

      - name: Prepare database
        run: flask db upgrade

      - name: Start Flask dev server
        run: flask run --port 5000 &
        # Allow a moment for the server to be ready; the E2E conftest
        # should also implement a readiness check/retry loop.

      - name: Wait for Flask to be ready
        run: |
          for i in $(seq 1 10); do
            curl -sf http://localhost:5000/health && break
            echo "Waiting for Flask... ($i)"
            sleep 2
          done

      - name: Run E2E tests
        run: |
          pytest tests/e2e/ \
            -m e2e \
            --tracing=retain-on-failure \
            --screenshot=only-on-failure \
            --output=test-results \
            -v

      - name: Upload Playwright artifacts
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-artifacts
          path: |
            test-results/
          retention-days: 7
```

---

## 11. Quick Checklist

Before merging a new CI workflow:

- [ ] `concurrency` block cancels stale PR runs (`cancel-in-progress: true`)
- [ ] Secrets accessed via `${{ secrets.NAME }}`, never hardcoded
- [ ] `fail-fast: false` on multi-version matrix
- [ ] Coverage threshold set and enforced (`--cov-fail-under`)
- [ ] Playwright `--with-deps` used (not just `playwright install`)
- [ ] Artifact upload scoped to `if: failure()` to avoid noise
- [ ] Database health check `options:` on the service container
- [ ] Migrations run before any test step that touches the DB
- [ ] Lint job runs before (or in parallel to) test jobs
- [ ] `actions/cache` keys include file hashes, not static strings

---

## References

- [pytest-cov docs](https://pytest-cov.readthedocs.io/)
- [Playwright Python CI docs](https://playwright.dev/python/docs/ci)
- [Ruff configuration reference](https://docs.astral.sh/ruff/configuration/)
- [tox-gh-actions](https://github.com/ymyzk/tox-gh-actions)
- [actions/cache](https://github.com/actions/cache)
- [GitHub Actions: service containers](https://docs.github.com/en/actions/use-cases-and-examples/using-containerized-services/about-service-containers)
