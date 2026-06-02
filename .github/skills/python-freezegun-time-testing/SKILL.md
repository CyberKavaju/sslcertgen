---
name: python-freezegun-time-testing
description: 'Test time-dependent Python and Flask code with freezegun. Use when freezing current time, validating expiration logic, asserting created_at/updated_at behavior, testing date filters, handling timezone-aware datetimes, and combining freezegun with pytest fixtures.'
argument-hint: 'Share your stack (Flask/SQLAlchemy/plain Python), timezone policy (UTC/local), and target behavior (expiry/audit fields/date ranges).'
user-invocable: true
---

# Time-Dependent Python Testing With freezegun

## What This Skill Produces
- Stable, deterministic tests for time-sensitive logic.
- Repeatable patterns for expiration windows, audit timestamps, and date-based querying.
- Flask examples that show how frozen time interacts with request handling.
- Safe patterns for timezone-aware datetimes and UTC normalization.

## When To Use
- Business logic depends on "now" or "today".
- Expiration rules fail intermittently based on wall-clock time.
- Models include `created_at` / `updated_at` fields.
- Endpoints support date-range filtering.
- Your tests need to validate UTC-aware behavior across timezones.

## Prerequisites

```bash
python -m pip install -U pytest freezegun
```

For Flask + SQLAlchemy projects:

```bash
python -m pip install -U flask sqlalchemy
```

## Core Rules
1. Freeze time where it is consumed, not only where it is defined.
2. Prefer timezone-aware datetimes (`datetime.now(timezone.utc)`) in production code.
3. Keep assertions explicit about timezone and boundary inclusivity.
4. Avoid mixing naive and aware datetimes in comparisons.
5. Use fixture-driven setup so the same frozen clock policy is reused.

---

## 1. Freeze Current Time Correctly

Use `@freeze_time` for small tests and context managers for narrower scope.

```python
from datetime import datetime, timezone
from freezegun import freeze_time


@freeze_time("2026-05-01T12:00:00Z")
def test_now_is_stable():
    now = datetime.now(timezone.utc)
    assert now.isoformat() == "2026-05-01T12:00:00+00:00"
```

Narrow-scope freezing:

```python
from datetime import datetime, timezone
from freezegun import freeze_time


def test_partial_freeze_scope():
    before = datetime.now(timezone.utc)

    with freeze_time("2026-05-01T08:30:00Z"):
        during = datetime.now(timezone.utc)
        assert during.hour == 8

    after = datetime.now(timezone.utc)
    assert after >= before
```

---

## 2. Test Expiration Logic

Write edge tests for exact boundary, just before, and just after expiry.

```python
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time


@dataclass
class Token:
    issued_at: datetime
    ttl_seconds: int

    def is_expired(self, now: datetime) -> bool:
        return now >= self.issued_at + timedelta(seconds=self.ttl_seconds)


@freeze_time("2026-05-01T10:00:00Z")
def test_token_not_expired_just_before_boundary():
    issued = datetime.now(timezone.utc)
    token = Token(issued_at=issued, ttl_seconds=300)

    with freeze_time("2026-05-01T10:04:59Z"):
        assert token.is_expired(datetime.now(timezone.utc)) is False


@freeze_time("2026-05-01T10:00:00Z")
def test_token_expired_on_boundary():
    issued = datetime.now(timezone.utc)
    token = Token(issued_at=issued, ttl_seconds=300)

    with freeze_time("2026-05-01T10:05:00Z"):
        assert token.is_expired(datetime.now(timezone.utc)) is True
```

Checklist:
- Test `now == expires_at` behavior explicitly.
- Confirm your intended comparison operator (`>` vs `>=`).
- Add one test immediately before and after the cutoff.

---

## 3. Test `created_at` And `updated_at`

Validate initial insert timestamps and update-time changes separately.

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from freezegun import freeze_time


@dataclass
class Record:
    name: str
    created_at: datetime
    updated_at: datetime

    def rename(self, new_name: str, now: datetime) -> None:
        self.name = new_name
        self.updated_at = now


@freeze_time("2026-05-01T09:00:00Z")
def test_created_and_updated_equal_on_create():
    now = datetime.now(timezone.utc)
    rec = Record(name="draft", created_at=now, updated_at=now)
    assert rec.created_at == rec.updated_at


@freeze_time("2026-05-01T09:00:00Z")
def test_updated_at_changes_on_mutation():
    start = datetime.now(timezone.utc)
    rec = Record(name="draft", created_at=start, updated_at=start)

    with freeze_time("2026-05-01T09:10:00Z"):
        rec.rename("published", datetime.now(timezone.utc))

    assert rec.created_at.isoformat() == "2026-05-01T09:00:00+00:00"
    assert rec.updated_at.isoformat() == "2026-05-01T09:10:00+00:00"
```

If your ORM auto-updates `updated_at`, flush/commit within the frozen block so hooks run under expected time.

---

## 4. Test Date Filters

Date filtering should be tested with known fixture timestamps and clear inclusive/exclusive boundaries.

```python
from datetime import datetime, timezone


def test_filter_from_to_inclusive(report_repo):
    items = [
        report_repo.create(created_at=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)),
        report_repo.create(created_at=datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)),
        report_repo.create(created_at=datetime(2026, 5, 3, 23, 59, tzinfo=timezone.utc)),
    ]

    result = report_repo.list_between(
        start=datetime(2026, 5, 2, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 5, 3, 0, 0, tzinfo=timezone.utc),
    )

    assert [x.id for x in result] == [items[1].id]
```

Guidance:
- Test midnight boundaries (`00:00:00`) and end-of-day behavior.
- Normalize incoming API dates to UTC before querying.
- Document whether end date is inclusive or exclusive.

---

## 5. Timezone Considerations

Preferred production pattern:

```python
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
```

Test a timezone conversion boundary:

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from freezegun import freeze_time


@freeze_time("2026-11-01T08:30:00Z")
def test_utc_to_local_conversion_is_explicit():
    now_utc = datetime.now(timezone.utc)
    los_angeles = now_utc.astimezone(ZoneInfo("America/Los_Angeles"))

    assert now_utc.tzinfo == timezone.utc
    assert los_angeles.tzinfo is not None
```

Timezone checklist:
- Store and compare in UTC when possible.
- Convert to local zone only at presentation boundaries.
- Never compare naive to aware datetimes.

---

## 6. Flask Request Lifecycle Examples

Freeze time around request handling to validate route-level logic that reads current time.

```python
from datetime import datetime, timezone
from freezegun import freeze_time


@freeze_time("2026-05-01T14:00:00Z")
def test_login_sets_session_expiry(client):
    resp = client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["session_expires_at"] == "2026-05-01T15:00:00+00:00"
```

For hook-based timestamps (`before_request`, `after_request`), keep the whole request in the frozen context so all hooks share one consistent clock.

```python
from freezegun import freeze_time


def test_request_audit_timestamp(client):
    with freeze_time("2026-05-01T15:45:00Z"):
        resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.headers["X-Processed-At"] == "2026-05-01T15:45:00+00:00"
```

---

## 7. Combine freezegun With pytest Fixtures

Use reusable fixtures for default frozen clocks and opt out per test when needed.

```python
# tests/conftest.py
import pytest
from freezegun import freeze_time


@pytest.fixture
def frozen_now():
    with freeze_time("2026-05-01T00:00:00Z") as frozen:
        yield frozen
```

```python
from datetime import datetime, timezone


def test_with_shared_frozen_fixture(frozen_now):
    assert datetime.now(timezone.utc).isoformat() == "2026-05-01T00:00:00+00:00"

    frozen_now.move_to("2026-05-01T00:10:00Z")
    assert datetime.now(timezone.utc).isoformat() == "2026-05-01T00:10:00+00:00"
```

Fixture tips:
- Keep fixture scope as `function` to avoid cross-test leakage.
- Use named fixtures (`frozen_now`, `frozen_deadline`) to clarify intent.
- For complex suites, centralize freeze policy in `tests/conftest.py`.

---

## 8. Common Mistakes And Fixes

### Mistake: Calling `datetime.now()` directly in many places
Fix: Route through a small clock function and patch/freeze at that boundary.

### Mistake: Using `date.today()` while app logic uses UTC datetimes
Fix: Derive dates from UTC datetime in one place; assert date boundaries in UTC.

### Mistake: Mixing naive and aware datetimes
Fix: Ensure all persisted/comparison datetimes include timezone (`timezone.utc`).

### Mistake: Freezing after object creation
Fix: Freeze before constructing time-dependent objects so issued timestamps are deterministic.

### Mistake: Expiry tests only cover happy path
Fix: Add boundary tests for just-before, exact, and just-after expiration.

---

## Completion Checks
- Tests pass repeatedly without clock-related flakiness.
- Expiration logic has boundary coverage (`-1s`, exact, `+1s`).
- `created_at` and `updated_at` behavior is validated on create and update.
- Date filter tests explicitly document inclusive/exclusive behavior.
- Timezone policy is explicit and consistently asserted in tests.
- Flask request-level tests run with frozen time covering hooks and handlers.

## Suggested Prompts
- "Use `python-freezegun-time-testing` to add boundary tests for token expiration in my service layer."
- "Apply `python-freezegun-time-testing` to verify `created_at`/`updated_at` in my SQLAlchemy models."
- "Use `python-freezegun-time-testing` to harden date-range filter tests for my Flask endpoint."