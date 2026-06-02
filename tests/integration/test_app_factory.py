import pytest

from app import create_app


@pytest.mark.integration
def test_create_app_uses_testing_config() -> None:
    app = create_app("testing")

    assert app.config["TESTING"] is True


@pytest.mark.integration
def test_healthz_endpoint_returns_ok(client) -> None:

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


@pytest.mark.integration
def test_security_headers_are_applied_by_default(client) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'" in csp
    assert "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com" in csp
    assert "font-src 'self' https://fonts.gstatic.com" in csp
    assert "img-src 'self' data:" in csp
    assert "connect-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'none'" in csp
    assert "form-action 'self'" in csp
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.integration
def test_root_route_keeps_security_headers(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" in response.headers
