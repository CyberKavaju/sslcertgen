---
name: python-factory-boy-test-data
description: 'Reusable test data management for Python with factory-boy in Flask MVC and SQLAlchemy projects. Use when deciding factories vs fixtures, modeling relationships, generating deterministic fake data, integrating DB sessions, and avoiding brittle hardcoded fixtures.'
argument-hint: 'Share your models (User/Role/Permission/domain), DB strategy, and determinism needs (seeded/unseeded).'
user-invocable: true
---

# Python factory-boy Test Data Management

## What This Skill Produces
- A repeatable strategy for creating maintainable test data in Python.
- Clear decision rules for factories vs pytest fixtures.
- Factory structure patterns for Flask MVC with SQLAlchemy-style models.
- Identity/access factories (`User`, `Role`, `Permission`) plus domain factories.
- Relationship patterns that stay realistic without brittle hardcoded values.
- Deterministic test data controls for stable CI and local runs.

## When To Use
- You are writing or refactoring tests in Flask MVC apps with SQLAlchemy.
- Test setup is repetitive, fragile, or tightly coupled to hardcoded values.
- You need realistic but controlled data for unit/integration tests.
- You need reproducible failures and deterministic data generation in CI.

## Decision Guide: Factories vs Fixtures

Use **factory-boy factories** when:
- You need many variations of the same model.
- You need composable object graphs (subfactories and related records).
- You need readable per-test overrides (`UserFactory(is_active=False)`).
- You want realistic defaults and optional trait-style behavior.

Use **pytest fixtures** when:
- You need environment/test harness setup (app, DB session, client, monkeypatch).
- You need lifecycle management (`setup/teardown`, transactions, rollbacks).
- You need scenario-level composition (for example, "admin user with 2 posts").

Use **both together** by default:
- Fixtures provide boundaries and lifecycle.
- Factories provide flexible data creation inside those boundaries.

## Completion Criteria
- Tests no longer depend on magic primary keys or fixed timestamps unless intentional.
- Data setup is readable in one pass and focused on behavior under test.
- Object relationships are valid by construction.
- Test runs are deterministic when seeded.
- Failures identify behavior regressions, not random data noise.

## Procedure

### 1. Define the Model Graph Before Writing Factories
Map core relationships first:
- `User` many-to-many `Role`
- `Role` many-to-many `Permission`
- Domain model owned by `User` (for example `Project`, `Ticket`, `Order`)

This prevents circular factory mistakes and duplicated setup helpers.

### 2. Create a Shared SQLAlchemy Factory Base
Use one base class so all factories share the same SQLAlchemy session behavior.

```python
import factory
from factory.alchemy import SQLAlchemyModelFactory


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "flush"
```

Guidance:
- Set `sqlalchemy_session` from pytest fixture, not global module state.
- Prefer `flush` for speed; use `commit` only when test behavior requires committed rows.

### 3. Build Identity and Access Factories

Example SQLAlchemy-style models:

```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
```

Factories:

```python
import factory
from factory import Faker


class PermissionFactory(BaseFactory):
    class Meta:
        model = Permission

    code = factory.Sequence(lambda n: f"perm:{n:04d}")


class RoleFactory(BaseFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"role_{n:03d}")

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for perm in extracted:
                self.permissions.append(perm)


class UserFactory(BaseFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n:04d}@example.test")
    name = Faker("name")
    is_active = True

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for role in extracted:
                self.roles.append(role)
```

### 4. Add Domain Object Factories With Realistic Relationships

Example domain model:

```python
from sqlalchemy import DateTime, Text
from datetime import datetime


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
```

Factory:

```python
class ProjectFactory(BaseFactory):
    class Meta:
        model = Project

    slug = factory.Sequence(lambda n: f"project-{n:04d}")
    title = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("paragraph", nb_sentences=2)
    owner = factory.SubFactory(UserFactory)
```

Pattern:
- Use `SubFactory` for required foreign keys.
- Override in tests only what matters for that behavior.

### 5. Use Fake Data Patterns Intentionally
Recommended defaults:
- Use `Sequence` for uniqueness-sensitive fields (`email`, `slug`, `code`).
- Use `Faker` for human-readable fields where uniqueness is not mandatory.
- Use `LazyAttribute` when one field depends on another.

Example:

```python
class TicketFactory(BaseFactory):
    class Meta:
        model = Ticket

    title = factory.Faker("sentence", nb_words=5)
    slug = factory.LazyAttribute(lambda o: o.title.lower().replace(" ", "-")[:48])
```

Avoid:
- Hardcoding repeated literals in many tests (`"alice@example.com"`, `"admin"`, `id=1`).
- Random values in assertions without deterministic controls.

### 6. Make Data Deterministic for Stable Tests
For deterministic runs, seed all randomness sources in one fixture.

```python
import random
import factory
from faker import Faker


def seed_test_data(seed: int = 4242) -> None:
    random.seed(seed)
    Faker.seed(seed)
    factory.random.reseed_random(seed)
```

Tips:
- Call seeding early in session setup.
- If a test requires explicit values, override factory fields directly.
- For snapshot tests, avoid unstable faker providers (for example, datetime-now).

### 7. Integrate Factories With DB Session Fixtures
Wire the SQLAlchemy session through pytest fixtures, then inject into all factories.

```python
import pytest


@pytest.fixture
def db_session(session):
    # "session" here is your SQLAlchemy session fixture.
    BaseFactory._meta.sqlalchemy_session = session
    yield session
    session.rollback()


@pytest.fixture(autouse=True)
def _seed_data():
    seed_test_data(4242)
```

If you use nested transactions:
- Bind factory session to the per-test transaction/session.
- Keep test isolation at function scope.

### 8. Compose Scenario Fixtures, Not Raw Objects Everywhere
Keep complex arrangements in named fixtures that still use factories internally.

```python
@pytest.fixture
def admin_user(db_session):
    manage_users = PermissionFactory(code="users:manage")
    admin_role = RoleFactory(name="admin", permissions=[manage_users])
    return UserFactory(roles=[admin_role])


@pytest.fixture
def owned_project(db_session, admin_user):
    return ProjectFactory(owner=admin_user)
```

This keeps tests short while avoiding giant globally shared fixtures.

### 9. Prefer Behavior-Centric Assertions Over Static Values

Better:
- Assert role membership, permission checks, ownership, status changes.
- Assert unique constraints and relationship integrity.

Avoid:
- Asserting exact generated names/text unless the value itself is behavior-critical.

## Example Test Patterns

### Unit-Level Service Test

```python
def test_user_can_manage_users_when_permission_present(db_session):
    perm = PermissionFactory(code="users:manage")
    role = RoleFactory(permissions=[perm])
    user = UserFactory(roles=[role])

    assert user_has_permission(user, "users:manage") is True
```

### Integration Test With Domain Relationship

```python
def test_project_owner_is_persisted(db_session):
    owner = UserFactory()
    project = ProjectFactory(owner=owner)

    db_session.flush()

    assert project.owner_id == owner.id
    assert project.owner.email.endswith("@example.test")
```

## Anti-Brittle Checklist
- No tests require a fixed primary key like `id == 1`.
- No repeated hardcoded emails/usernames spread across files.
- Relationship creation happens via factories, not manual FK assignment strings.
- Tests override only relevant fields for readability.
- Deterministic seed strategy is documented and enabled.

## Common Branching Decisions
- Need one object with slight variation: call factory with overrides.
- Need many related records: use `SubFactory`, `post_generation`, or scenario fixture.
- Need strict expected value: override specific field directly, avoid random provider.
- Need app/DB/client setup: use fixtures, not factories.

## Suggested Prompt Starters
- "Use python-factory-boy-test-data to design factories for User, Role, Permission, and Project models."
- "Refactor my brittle pytest data setup into fixture + factory-boy patterns with deterministic seeding."
- "Generate SQLAlchemy factory examples for many-to-many roles and permissions in Flask MVC tests."