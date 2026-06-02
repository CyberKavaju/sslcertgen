from datetime import timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

from app.schemas.certificate_schema import CertificatePolicy
from app.services.certificate_service import CertificateGenerationError, generate_certificate
from app.utils.fqdn_validator import InvalidFQDNError


@pytest.mark.unit
def test_generate_certificate_default_policy_returns_parseable_pem() -> None:
    result = generate_certificate("example.com")

    cert = x509.load_pem_x509_certificate(result.certificate_pem.encode("ascii"))
    key = serialization.load_pem_private_key(result.private_key_pem.encode("ascii"), password=None)

    subject_cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    san_extension = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
    san_names = san_extension.value.get_values_for_type(x509.DNSName)

    assert subject_cn == "example.com"
    assert san_names == ["example.com"]
    assert isinstance(key, rsa.RSAPrivateKey)


@pytest.mark.unit
def test_generate_certificate_ec_policy_returns_ec_key() -> None:
    policy = CertificatePolicy(algorithm="EC", rsa_key_size=None, ec_curve="P-256")

    result = generate_certificate("example.com", policy=policy)

    key = serialization.load_pem_private_key(result.private_key_pem.encode("ascii"), password=None)
    assert isinstance(key, ec.EllipticCurvePrivateKey)


@pytest.mark.unit
def test_generate_certificate_applies_validity_window() -> None:
    policy = CertificatePolicy(validity_days=30)

    result = generate_certificate("example.com", policy=policy)
    cert = x509.load_pem_x509_certificate(result.certificate_pem.encode("ascii"))

    validity = cert.not_valid_after - cert.not_valid_before
    assert timedelta(days=29) <= validity <= timedelta(days=31)


@pytest.mark.unit
def test_generate_certificate_invalid_domain_raises_invalid_fqdn_error() -> None:
    with pytest.raises(InvalidFQDNError):
        generate_certificate("bad domain.com")


@pytest.mark.unit
def test_generate_certificate_wraps_cryptography_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_value_error(*args: object, **kwargs: object) -> object:
        raise ValueError("low-level details")

    monkeypatch.setattr(
        "app.services.certificate_service.rsa.generate_private_key", _raise_value_error
    )

    with pytest.raises(CertificateGenerationError) as exc_info:
        generate_certificate("example.com")

    message = str(exc_info.value)
    assert "low-level details" not in message
