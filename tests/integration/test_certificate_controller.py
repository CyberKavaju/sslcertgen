import logging

import pytest

from app.services import certificate_service


@pytest.mark.integration
def test_generate_valid_domain_returns_pem_payload(client) -> None:
    response = client.post("/api/v1/generate", json={"domain": "example.com"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["certificate"].startswith("-----BEGIN CERTIFICATE-----")
    assert payload["certificate"].strip().endswith("-----END CERTIFICATE-----")
    assert payload["key"].startswith("-----BEGIN PRIVATE KEY-----")
    assert payload["key"].strip().endswith("-----END PRIVATE KEY-----")


@pytest.mark.integration
def test_generate_rejects_non_json_content_type(client) -> None:
    response = client.post("/api/v1/generate", data="domain=example.com")

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_request",
        "message": "Request body must be valid JSON",
    }


@pytest.mark.integration
def test_generate_rejects_invalid_json_body(client) -> None:
    response = client.post(
        "/api/v1/generate",
        data='{"domain": "example.com"',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_request",
        "message": "Request body must be valid JSON",
    }


@pytest.mark.integration
def test_generate_requires_domain_field(client) -> None:
    response = client.post("/api/v1/generate", json={})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_request",
        "message": "domain is required",
        "details": {"domain": "domain is required"},
    }


@pytest.mark.integration
def test_generate_rejects_policy_field_in_phase_two(client) -> None:
    response = client.post(
        "/api/v1/generate",
        json={"domain": "example.com", "policy": {"algorithm": "RSA"}},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_request",
        "message": "policy is not supported in Phase 2",
        "details": {"policy": "policy is not supported in Phase 2"},
    }


@pytest.mark.integration
def test_generate_rejects_invalid_domain(client) -> None:
    response = client.post("/api/v1/generate", json={"domain": "bad domain"})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_domain",
        "message": "Domain is invalid",
    }


@pytest.mark.integration
def test_generate_maps_certificate_generation_error_to_500(client, monkeypatch) -> None:
    def _raise_generation_error(*_args, **_kwargs):
        raise certificate_service.CertificateGenerationError("internal detail")

    monkeypatch.setattr(certificate_service, "generate_certificate", _raise_generation_error)

    response = client.post("/api/v1/generate", json={"domain": "example.com"})

    assert response.status_code == 500
    assert response.get_json() == {
        "error": "generation_failed",
        "message": "Certificate generation failed",
    }


@pytest.mark.integration
def test_generate_maps_unexpected_service_exception_to_500(client, monkeypatch) -> None:
    def _raise_unexpected(*_args, **_kwargs):
        raise TimeoutError("service timeout")

    monkeypatch.setattr(certificate_service, "generate_certificate", _raise_unexpected)

    response = client.post("/api/v1/generate", json={"domain": "example.com"})

    assert response.status_code == 500
    assert response.get_json() == {
        "error": "generation_failed",
        "message": "Certificate generation failed",
    }


@pytest.mark.integration
def test_generate_get_method_returns_standardized_405(client) -> None:
    response = client.get("/api/v1/generate")

    assert response.status_code == 405
    assert response.get_json() == {
        "error": "method_not_allowed",
        "message": "Method not allowed",
    }


@pytest.mark.integration
def test_unknown_route_returns_standardized_404(client) -> None:
    response = client.get("/api/v1/not-real")

    assert response.status_code == 404
    assert response.get_json() == {
        "error": "not_found",
        "message": "Resource not found",
    }


@pytest.mark.integration
def test_generate_rate_limited_returns_429_contract(client_factory) -> None:
    client = client_factory(env={"RATE_LIMIT_PER_IP": "1/minute"})

    first = client.post(
        "/api/v1/generate",
        json={"domain": "example.com"},
        headers={"X-Forwarded-For": "203.0.113.10"},
    )
    second = client.post(
        "/api/v1/generate",
        json={"domain": "example.com"},
        headers={"X-Forwarded-For": "203.0.113.10"},
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.get_json() == {
        "error": "rate_limited",
        "message": "Too many requests",
    }


@pytest.mark.integration
def test_generate_rate_limit_isolated_by_ip(client_factory) -> None:
    client = client_factory(env={"RATE_LIMIT_PER_IP": "1/minute"})

    first_ip_first = client.post(
        "/api/v1/generate",
        json={"domain": "example.com"},
        headers={"X-Forwarded-For": "203.0.113.11"},
    )
    first_ip_second = client.post(
        "/api/v1/generate",
        json={"domain": "example.com"},
        headers={"X-Forwarded-For": "203.0.113.11"},
    )
    second_ip_first = client.post(
        "/api/v1/generate",
        json={"domain": "example.com"},
        headers={"X-Forwarded-For": "203.0.113.12"},
    )

    assert first_ip_first.status_code == 200
    assert first_ip_second.status_code == 429
    assert second_ip_first.status_code == 200


@pytest.mark.integration
def test_generate_rate_limit_allows_requests_under_threshold(client_factory) -> None:
    client = client_factory(env={"RATE_LIMIT_PER_IP": "2/minute"})

    first = client.post(
        "/api/v1/generate",
        json={"domain": "example.com"},
        headers={"X-Forwarded-For": "203.0.113.13"},
    )
    second = client.post(
        "/api/v1/generate",
        json={"domain": "example.com"},
        headers={"X-Forwarded-For": "203.0.113.13"},
    )

    assert first.status_code == 200
    assert second.status_code == 200


@pytest.mark.integration
def test_generate_oversized_payload_returns_413(client) -> None:
    oversized_body = "{" + '"domain": "' + ("a" * 9000) + '"}'

    response = client.post(
        "/api/v1/generate",
        data=oversized_body,
        content_type="application/json",
    )

    assert response.status_code == 413
    assert response.get_json() == {
        "error": "payload_too_large",
        "message": "Request payload is too large",
    }


@pytest.mark.integration
def test_generate_rejects_unknown_fields(client) -> None:
    response = client.post(
        "/api/v1/generate",
        json={"domain": "example.com", "extra": "value"},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_request",
        "message": "unknown fields are not allowed",
        "details": {"extra": "unknown field"},
    }


@pytest.mark.integration
def test_generate_rejects_domain_longer_than_253(client) -> None:
    too_long_domain = f"{'a' * 64}.{'b' * 64}.{'c' * 64}.{'d' * 61}"

    response = client.post("/api/v1/generate", json={"domain": too_long_domain})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_request",
        "message": "domain must be at most 253 characters",
        "details": {"domain": "domain must be at most 253 characters"},
    }


@pytest.mark.integration
def test_generate_rejects_empty_json_body(client) -> None:
    response = client.post(
        "/api/v1/generate",
        data="",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "invalid_request",
        "message": "Request body must be valid JSON",
    }


@pytest.mark.integration
def test_generate_failure_path_logs_do_not_include_private_key_markers(
    client, monkeypatch, caplog
) -> None:
    def _raise_unexpected(*_args, **_kwargs):
        raise RuntimeError("-----BEGIN PRIVATE KEY----- leaked -----END PRIVATE KEY-----")

    monkeypatch.setattr(certificate_service, "generate_certificate", _raise_unexpected)
    caplog.set_level(logging.ERROR)

    response = client.post("/api/v1/generate", json={"domain": "example.com"})

    assert response.status_code == 500
    assert "BEGIN PRIVATE KEY" not in caplog.text
    assert "END PRIVATE KEY" not in caplog.text


@pytest.mark.integration
def test_generate_success_path_logs_do_not_include_private_key_markers(client, caplog) -> None:
    caplog.set_level(logging.INFO)

    response = client.post("/api/v1/generate", json={"domain": "example.com"})

    assert response.status_code == 200
    assert "BEGIN PRIVATE KEY" not in caplog.text
    assert "END PRIVATE KEY" not in caplog.text
