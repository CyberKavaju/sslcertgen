from dataclasses import dataclass
from typing import Literal


_SENSITIVE_MARKERS = (
    "-----BEGIN PRIVATE KEY-----",
    "-----END PRIVATE KEY-----",
)


def redact_sensitive_text(value: str) -> str:
    redacted = value
    for marker in _SENSITIVE_MARKERS:
        redacted = redacted.replace(marker, "[redacted]")
    return redacted


def redact_details(details: dict[str, str] | None) -> dict[str, str] | None:
    if details is None:
        return None
    return {key: redact_sensitive_text(str(value)) for key, value in details.items()}


class PolicyValidationError(ValueError):
    """Raised when certificate policy settings are invalid."""


class RequestValidationError(ValueError):
    """Raised when an API request payload is invalid."""

    def __init__(self, message: str, details: dict[str, str] | None = None):
        super().__init__(message)
        self.details = details


class ApiException(Exception):
    """Raised when API requests should return a structured error payload."""

    def __init__(
        self,
        *,
        error: str,
        message: str,
        status_code: int,
        details: dict[str, str] | None = None,
    ):
        super().__init__(message)
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details


class RateLimitError(ApiException):
    """Raised when a request exceeds rate limiting."""

    def __init__(self):
        super().__init__(error="rate_limited", message="Too many requests", status_code=429)


@dataclass(frozen=True)
class CertificatePolicy:
    algorithm: Literal["RSA", "EC"] = "RSA"
    rsa_key_size: int | None = 2048
    ec_curve: Literal["P-256", "P-384"] | None = None
    validity_days: int = 365
    subject_organization: str | None = None
    subject_organizational_unit: str | None = None
    subject_country: str | None = None
    san_dns_names: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.algorithm not in {"RSA", "EC"}:
            raise PolicyValidationError("Invalid certificate policy: unsupported algorithm")

        if self.algorithm == "RSA":
            if self.ec_curve is not None:
                raise PolicyValidationError(
                    "Invalid certificate policy: ec_curve not allowed for RSA"
                )
            if self.rsa_key_size not in {2048, 3072, 4096}:
                raise PolicyValidationError("Invalid certificate policy: unsupported RSA key size")

        if self.algorithm == "EC":
            if self.rsa_key_size is not None:
                raise PolicyValidationError(
                    "Invalid certificate policy: rsa_key_size not allowed for EC"
                )
            if self.ec_curve not in {"P-256", "P-384"}:
                raise PolicyValidationError("Invalid certificate policy: unsupported EC curve")

        if not 1 <= self.validity_days <= 825:
            raise PolicyValidationError(
                "Invalid certificate policy: validity_days must be in 1..825"
            )

        if self.subject_organization is not None and len(self.subject_organization) > 64:
            raise PolicyValidationError("Invalid certificate policy: O must be <= 64 characters")

        if (
            self.subject_organizational_unit is not None
            and len(self.subject_organizational_unit) > 64
        ):
            raise PolicyValidationError("Invalid certificate policy: OU must be <= 64 characters")

        if self.subject_country is not None:
            if len(self.subject_country) != 2 or not self.subject_country.isalpha():
                raise PolicyValidationError(
                    "Invalid certificate policy: C must be two alphabetic characters"
                )

        if self.san_dns_names is not None and len(self.san_dns_names) > 1:
            raise PolicyValidationError(
                "Invalid certificate policy: Phase 1 supports primary domain SAN only"
            )


@dataclass(frozen=True)
class CertificateServiceResult:
    certificate_pem: str
    private_key_pem: str

    def __repr__(self) -> str:
        return "CertificateServiceResult(certificate_pem=<redacted>, private_key_pem=<redacted>)"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass(frozen=True)
class CertificateResponse:
    certificate: str
    key: str

    @classmethod
    def from_service_result(cls, result: CertificateServiceResult) -> "CertificateResponse":
        return cls(certificate=result.certificate_pem, key=result.private_key_pem)

    def __repr__(self) -> str:
        return "CertificateResponse(certificate=<redacted>, key=<redacted>)"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass(frozen=True)
class ApiErrorResponse:
    error: str
    message: str
    details: dict[str, str] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "error": self.error,
            "message": self.message,
        }
        safe_details = redact_details(self.details)
        if safe_details is not None:
            payload["details"] = safe_details
        return payload


@dataclass(frozen=True)
class GenerateCertificateRequest:
    domain: str

    @classmethod
    def from_payload(
        cls,
        payload: object,
        *,
        max_domain_length: int = 253,
    ) -> "GenerateCertificateRequest":
        if not isinstance(payload, dict):
            raise RequestValidationError("Request payload must be a JSON object")

        if "policy" in payload:
            message = "policy is not supported in Phase 2"
            raise RequestValidationError(message, details={"policy": message})

        unknown_fields = [field for field in payload.keys() if field != "domain"]
        if unknown_fields:
            details = {field: "unknown field" for field in sorted(unknown_fields)}
            raise RequestValidationError("unknown fields are not allowed", details=details)

        domain = payload.get("domain")
        if not isinstance(domain, str):
            message = "domain is required"
            raise RequestValidationError(message, details={"domain": message})

        normalized_domain = domain.strip()
        if not normalized_domain:
            message = "domain is required"
            raise RequestValidationError(message, details={"domain": message})

        if len(normalized_domain) > max_domain_length:
            message = f"domain must be at most {max_domain_length} characters"
            raise RequestValidationError(message, details={"domain": message})

        return cls(domain=normalized_domain)
