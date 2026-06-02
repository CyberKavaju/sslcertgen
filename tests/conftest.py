import pytest

from app import create_app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "memory://")
    return create_app("testing")


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def client_factory(monkeypatch: pytest.MonkeyPatch):
    def _factory(*, env: dict[str, str] | None = None):
        if env:
            for key, value in env.items():
                monkeypatch.setenv(key, value)
        app = create_app("testing")
        return app.test_client()

    return _factory
