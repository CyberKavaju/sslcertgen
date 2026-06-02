---
name: testing-master-index
description: 'Master index for Python Flask MVC testing skills. Use when choosing testing-core-pytest, testing-flask-mvc, testing-e2e-playwright, testing-data-factories, testing-mocking-http, testing-time-control, testing-coverage-quality, and testing-ci-automation; includes adoption order, combinations, testing pyramid, setup levels, and command checklist.'
argument-hint: 'Testing goal (bug fix/feature/CI hardening) and target scope (unit/integration/e2e/full stack).'
user-invocable: true
---

# Python Flask MVC Testing Skill Index

Use this skill as the navigation hub for selecting and sequencing testing skills in a Flask MVC codebase.

## Recommended Order Of Adoption
1. testing-core-pytest
2. testing-flask-mvc
3. testing-data-factories
4. testing-mocking-http
5. testing-time-control
6. testing-coverage-quality
7. testing-e2e-playwright
8. testing-ci-automation

## Skill Coverage And When To Use
| Skill | Primary coverage | Use when | Common pairings |
|---|---|---|---|
| testing-core-pytest | pytest config, fixtures, markers, test structure | Starting test foundation or fixing flaky baseline patterns | testing-coverage-quality, testing-ci-automation |
| testing-flask-mvc | Flask app factory tests, routes, services, DB integration boundaries | Verifying Flask request/response behavior and app-layer integration | testing-data-factories, testing-mocking-http |
| testing-e2e-playwright | Browser E2E for auth, forms, redirects, protected pages | Validating real user journeys across multiple pages | testing-data-factories, testing-ci-automation |
| testing-data-factories | factory-boy model graphs and deterministic data setup | Replacing brittle fixtures and hardcoded records | testing-flask-mvc, testing-e2e-playwright |
| testing-mocking-http | Mocking external dependencies and HTTP clients | Isolating outbound API behavior, retries, timeouts, failures | testing-core-pytest, testing-flask-mvc |
| testing-time-control | freezegun time freezing and boundary assertions | Testing expiry, audit timestamps, and date range logic | testing-core-pytest, testing-flask-mvc |
| testing-coverage-quality | Coverage targets, quality gates, marker policy, risk-based test depth | Enforcing measurable quality and reducing regression escape | testing-core-pytest, testing-ci-automation |
| testing-ci-automation | CI test orchestration, parallelization, artifact collection, gating | Making tests fast, repeatable, and enforceable in pipelines | testing-coverage-quality, testing-e2e-playwright |

## Common Skill Combinations By Task
| Task | Combine these skills |
|---|---|
| New Flask feature with DB changes | testing-core-pytest + testing-flask-mvc + testing-data-factories |
| External API integration with retries | testing-core-pytest + testing-mocking-http + testing-coverage-quality |
| Expiration and schedule logic | testing-core-pytest + testing-time-control + testing-flask-mvc |
| Critical user flow release hardening | testing-flask-mvc + testing-e2e-playwright + testing-ci-automation |
| Team-wide quality baseline rollout | testing-core-pytest + testing-coverage-quality + testing-ci-automation |

## Flask MVC Testing Pyramid
Target distribution by test count:
- Unit tests: 65 to 75 percent
- Integration tests (Flask routes, DB, service boundaries): 20 to 30 percent
- E2E browser tests: 5 to 10 percent

Mapping:
- Unit: testing-core-pytest, testing-time-control, testing-mocking-http
- Integration: testing-flask-mvc, testing-data-factories
- E2E: testing-e2e-playwright
- Governance across all layers: testing-coverage-quality, testing-ci-automation

## Minimum Viable Setup
Adopt first:
- testing-core-pytest
- testing-flask-mvc
- testing-data-factories

Minimum expectations:
- Working pytest configuration and markers
- App-factory based Flask test setup
- Deterministic factory-based test data
- CI executes unit and integration tests on every pull request

## Production-Grade Setup
Adopt all skills with these outcomes:
- Stable unit, integration, and E2E layers aligned to the testing pyramid
- Deterministic data and deterministic time behavior in business-critical tests
- Mocked external dependencies in unit/integration scope with clear boundary ownership
- Coverage and quality gates enforced in CI
- Browser E2E smoke path and release-critical flows in pipeline

## Commands Checklist
Use as a baseline and adapt to your project commands.

- Install test dependencies:
  - python -m pip install -U pytest pytest-cov
  - python -m pip install -U freezegun factory-boy
  - python -m pip install -U pytest-playwright playwright
  - python -m playwright install --with-deps chromium
- Run all tests:
  - pytest
- Run by layer:
  - pytest -m unit
  - pytest -m integration
  - pytest -m e2e
- Coverage gate:
  - pytest --cov=. --cov-report=term-missing --cov-fail-under=85
- CI-friendly output artifacts:
  - pytest --junitxml=reports/junit.xml --cov=. --cov-report=xml

## Suggested Prompt Starters
- Use testing-core-pytest to set up a clean pytest baseline for this Flask MVC project.
- Use testing-flask-mvc plus testing-data-factories for route and service integration tests for this feature.
- Use testing-time-control to add deterministic expiry boundary tests for token validation.
- Use testing-e2e-playwright and testing-ci-automation to add a CI-stable login smoke flow.
