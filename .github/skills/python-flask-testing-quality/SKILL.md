---
name: python-flask-testing-quality
description: 'Build and enforce Python Flask testing quality gates with coverage.py, pytest-cov, branch coverage, coverage thresholds, Ruff, mypy or pyright, pre-commit, and CI checks. Use when setting up or tightening quality standards for Flask projects.'
argument-hint: 'Python package path and desired coverage threshold (for example: app, 85)'
user-invocable: true
disable-model-invocation: false
---

# Python Flask Testing Quality

Create a reliable quality gate for Flask projects with copy-paste configuration and repeatable commands.

## When to Use
- You need a standard testing quality baseline for a Flask codebase.
- You want coverage with branch analysis and enforced thresholds.
- You want linting, formatting, and type checking to run locally and in CI.
- You want pre-commit checks to prevent low-quality commits.

## Inputs to Decide First
- Main import package name, referred to below as `<your_package>`.
- Coverage threshold target, default suggestion: `85`.
- Type checker choice: `mypy` (default) or `pyright`.

## Step 1: Install Quality Tooling

```bash
python -m pip install -U pytest pytest-cov coverage[toml] ruff mypy pre-commit
# Optional alternative type checker
python -m pip install -U pyright
```

## Step 2: Add Recommended pyproject.toml Configuration

Copy this into `pyproject.toml` and adjust `<your_package>` and threshold values.

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = [
  "-ra",
  "--strict-markers",
  "--strict-config",
  "--cov=<your_package>",
  "--cov-branch",
  "--cov-report=term-missing:skip-covered",
  "--cov-report=xml",
  "--cov-report=html",
  "--cov-fail-under=85"
]

[tool.coverage.run]
branch = true
source = ["<your_package>"]
omit = [
  "*/tests/*",
  "*/migrations/*",
  "*/alembic/*",
  "*/.venv/*",
  "*/site-packages/*",
  "*/__init__.py",
  "*/generated/*",
  "*/_generated/*"
]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = true
exclude_lines = [
  "pragma: no cover",
  "if TYPE_CHECKING:",
  'if __name__ == "__main__":',
  "raise NotImplementedError",
  "except ImportError"
]

[tool.ruff]
line-length = 100
target-version = "py311"
extend-exclude = ["migrations", "alembic", "generated", "_generated"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "W"]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"

[tool.mypy]
python_version = "3.11"
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
no_implicit_optional = true
strict_equality = true
check_untyped_defs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
pretty = true
exclude = "(?x)(^migrations/|^alembic/|^generated/|^_generated/)"
```

## Step 3: Optional Pyright Configuration (If You Choose Pyright)

Use this file only if you select pyright instead of mypy.

Create `pyrightconfig.json`:

```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.11",
  "include": ["<your_package>", "tests"],
  "exclude": [
    "**/migrations",
    "**/alembic",
    "**/generated",
    "**/_generated",
    "**/.venv"
  ],
  "reportMissingImports": true,
  "reportUnknownVariableType": true,
  "reportUnknownMemberType": true
}
```

## Step 4: Add Pre-commit Integration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.10
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0
    hooks:
      - id: mypy
        additional_dependencies: []
        args: [--config-file=pyproject.toml]

  - repo: local
    hooks:
      - id: pytest-quality
        name: pytest with coverage gate
        entry: pytest
        language: system
        pass_filenames: false
        stages: [pre-push]
        args:
          - --cov=<your_package>
          - --cov-branch
          - --cov-report=term-missing:skip-covered
          - --cov-fail-under=85
```

Enable hooks:

```bash
pre-commit install
pre-commit install --hook-type pre-push
pre-commit run --all-files
```

## Step 5: Local Development Commands

Fast inner loop:

```bash
ruff check .
ruff format .
pytest -q
```

Quality gate locally before pushing:

```bash
ruff check .
ruff format --check .
pytest --cov=<your_package> --cov-branch --cov-report=term-missing --cov-fail-under=85
mypy <your_package>
# or
pyright
```

Coverage report workflow:

```bash
coverage run -m pytest
coverage report -m
coverage html
```

## Step 6: CI Quality Gate Strategy

Use a dedicated quality job that fails the pipeline on any gate failure.

Create `.github/workflows/quality.yml`:

```yaml
name: quality

on:
  pull_request:
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install pytest pytest-cov coverage[toml] ruff mypy
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Ruff lint
        run: ruff check .

      - name: Ruff format check
        run: ruff format --check .

      - name: Tests with branch coverage gate
        run: pytest --cov=<your_package> --cov-branch --cov-report=xml --cov-report=term-missing --cov-fail-under=85

      - name: Type check (mypy)
        run: mypy <your_package>
```

## Branching Logic and Decisions
- If project has low initial coverage:
  1. Start with threshold `70`.
  2. Increase by 5 points every 1 to 2 sprints.
  3. Keep branch coverage enabled from day one.
- If codebase uses dynamic typing heavily:
  1. Use mypy with relaxed options first.
  2. Move toward strict options incrementally.
- If team prefers fast developer experience:
  1. Keep full pytest in pre-push.
  2. Keep only Ruff in pre-commit.

## Completion Criteria
- Coverage gate blocks merges below threshold.
- Branch coverage is enabled in both local and CI runs.
- Generated and irrelevant files are excluded from quality signals.
- Ruff check and format check both pass.
- One type checker gate (mypy or pyright) passes consistently.
- Pre-commit and pre-push hooks run successfully.

## Troubleshooting
- Coverage unexpectedly drops:
  1. Verify `source` and `omit` in coverage config.
  2. Confirm tests import real package modules, not duplicated paths.
- Mypy too noisy on legacy code:
  1. Scope checking to core package first.
  2. Tighten strictness in phases.
- CI differs from local:
  1. Ensure same Python versions and same tool versions.
  2. Keep CI commands identical to local gate command.

## Example Prompts
- `/python-flask-testing-quality package=app threshold=85`
- `Apply python-flask-testing-quality to this Flask repo with mypy strict mode.`
- `Use python-flask-testing-quality and set an initial threshold of 75 with a ramp plan.`
