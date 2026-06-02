import pytest

from app.schemas.certificate_schema import (
    ApiErrorResponse,
    CertificatePolicy,
    CertificateResponse,
    CertificateServiceResult,
    GenerateCertificateRequest,
    PolicyValidationError,
    RequestValidationError,
)


@pytest.mark.unit
def test_certificate_policy_default_values_are_valid() -> None:
    policy = CertificatePolicy()

    assert policy.algorithm == "RSA"
    assert policy.rsa_key_size == 2048
    assert policy.validity_days == 365


@pytest.mark.unit
@pytest.mark.parametrize("days", [0, 826])
def test_certificate_policy_validity_bounds(days: int) -> None:
    with pytest.raises(PolicyValidationError):
        CertificatePolicy(validity_days=days)


@pytest.mark.unit
def test_certificate_policy_rejects_rsa_with_curve() -> None:
    with pytest.raises(PolicyValidationError):
        CertificatePolicy(algorithm="RSA", ec_curve="P-256")


@pytest.mark.unit
def test_certificate_policy_rejects_ec_with_rsa_key_size() -> None:
    with pytest.raises(PolicyValidationError):
        CertificatePolicy(algorithm="EC", rsa_key_size=2048, ec_curve="P-256")


@pytest.mark.unit
def test_certificate_policy_rejects_invalid_subject_field_lengths() -> None:
    with pytest.raises(PolicyValidationError):
        CertificatePolicy(subject_organization="x" * 65)

    with pytest.raises(PolicyValidationError):
        CertificatePolicy(subject_organizational_unit="x" * 65)

    with pytest.raises(PolicyValidationError):
        CertificatePolicy(subject_country="USA")


@pytest.mark.unit
def test_certificate_response_maps_internal_service_result() -> None:
    internal = CertificateServiceResult(
        certificate_pem="-----BEGIN CERTIFICATE-----\\nabc\\n-----END CERTIFICATE-----\\n",
        private_key_pem="-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n",
    )

    response = CertificateResponse.from_service_result(internal)

    assert response.certificate == internal.certificate_pem
    assert response.key == internal.private_key_pem


@pytest.mark.unit
def test_certificate_response_repr_and_str_redact_private_key() -> None:
    response = CertificateResponse(
        certificate="-----BEGIN CERTIFICATE-----\\nabc\\n-----END CERTIFICATE-----\\n",
        key="-----BEGIN PRIVATE KEY-----\\nsecret\\n-----END PRIVATE KEY-----\\n",
    )

    assert "secret" not in repr(response)
    assert "secret" not in str(response)


@pytest.mark.unit
def test_generate_request_rejects_unknown_fields() -> None:
    with pytest.raises(RequestValidationError) as exc_info:
        GenerateCertificateRequest.from_payload({"domain": "example.com", "extra": "value"})

    assert str(exc_info.value) == "unknown fields are not allowed"
    assert exc_info.value.details == {"extra": "unknown field"}


@pytest.mark.unit
def test_generate_request_rejects_blank_domain() -> None:
    with pytest.raises(RequestValidationError) as exc_info:
        GenerateCertificateRequest.from_payload({"domain": "   "})

    assert str(exc_info.value) == "domain is required"
    assert exc_info.value.details == {"domain": "domain is required"}


@pytest.mark.unit
def test_generate_request_rejects_domain_longer_than_max() -> None:
    too_long_domain = f"{'a' * 64}.{'b' * 64}.{'c' * 64}.{'d' * 61}"

    with pytest.raises(RequestValidationError) as exc_info:
        GenerateCertificateRequest.from_payload(
            {"domain": too_long_domain},
            max_domain_length=253,
        )

    assert str(exc_info.value) == "domain must be at most 253 characters"
    assert exc_info.value.details == {"domain": "domain must be at most 253 characters"}


@pytest.mark.unit
def test_generate_request_strips_domain_whitespace() -> None:
    parsed = GenerateCertificateRequest.from_payload({"domain": "  example.com  "})

    assert parsed.domain == "example.com"


@pytest.mark.unit
def test_api_error_response_redacts_private_key_markers_from_details() -> None:
    payload = ApiErrorResponse(
        error="invalid_request",
        message="Request is invalid",
        details={
            "domain": "-----BEGIN PRIVATE KEY-----secret-----END PRIVATE KEY-----",
        },
    )

    serialized = payload.to_dict()

    assert serialized == {
        "error": "invalid_request",
        "message": "Request is invalid",
        "details": {"domain": "[redacted]secret[redacted]"},
    }
