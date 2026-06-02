from datetime import UTC, datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

from app.schemas.certificate_schema import (
    CertificatePolicy,
    CertificateServiceResult,
    PolicyValidationError,
)
from app.utils.fqdn_validator import validate_fqdn


class CertificateGenerationError(RuntimeError):
    """Raised when certificate generation fails after domain/policy validation."""


def _build_private_key(policy: CertificatePolicy):
    if policy.algorithm == "RSA":
        return rsa.generate_private_key(public_exponent=65537, key_size=policy.rsa_key_size or 2048)

    if policy.ec_curve == "P-384":
        return ec.generate_private_key(ec.SECP384R1())
    return ec.generate_private_key(ec.SECP256R1())


def _build_subject_name(canonical_domain: str, policy: CertificatePolicy) -> x509.Name:
    if len(canonical_domain) > 64:
        raise PolicyValidationError("Invalid certificate policy: CN must be <= 64 characters")

    attributes = [x509.NameAttribute(NameOID.COMMON_NAME, canonical_domain)]

    if policy.subject_organization:
        attributes.append(
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, policy.subject_organization)
        )

    if policy.subject_organizational_unit:
        attributes.append(
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, policy.subject_organizational_unit)
        )

    if policy.subject_country:
        attributes.append(x509.NameAttribute(NameOID.COUNTRY_NAME, policy.subject_country.upper()))

    return x509.Name(attributes)


def generate_certificate(
    domain: str, policy: CertificatePolicy | None = None
) -> CertificateServiceResult:
    """Generate self-signed certificate and key.

    Private keys are serialized as PKCS8 PEM with NoEncryption.
    Certificates are serialized as PEM.
    """
    active_policy = policy or CertificatePolicy()
    canonical_domain = validate_fqdn(domain)
    san_names = active_policy.san_dns_names or (canonical_domain,)

    if len(san_names) != 1:
        raise PolicyValidationError(
            "Invalid certificate policy: Phase 1 supports primary domain SAN only"
        )

    try:
        private_key = _build_private_key(active_policy)
        now = datetime.now(UTC)
        subject = _build_subject_name(canonical_domain, active_policy)

        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=active_policy.validity_days))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(canonical_domain)]), critical=False
            )
            .sign(private_key=private_key, algorithm=hashes.SHA256())
        )

        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM).decode("ascii")
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")
    except PolicyValidationError:
        raise
    except Exception as exc:  # pragma: no cover - explicit sanitization path tested via monkeypatch
        raise CertificateGenerationError("Certificate generation failed") from exc

    return CertificateServiceResult(
        certificate_pem=certificate_pem, private_key_pem=private_key_pem
    )
