from dataclasses import dataclass

from app.schemas.certificate_schema import RequestValidationError


@dataclass(frozen=True)
class WizardStartRequest:
    domain: str

    @classmethod
    def from_payload(
        cls,
        payload: object,
        *,
        max_domain_length: int,
    ) -> "WizardStartRequest":
        if not isinstance(payload, dict):
            raise RequestValidationError("Request payload must be a JSON object")

        unknown_fields = [field for field in payload.keys() if field != "domain"]
        if unknown_fields:
            details = {field: "unknown field" for field in sorted(unknown_fields)}
            raise RequestValidationError("unknown fields are not allowed", details=details)

        domain = payload.get("domain")
        if not isinstance(domain, str) or not domain.strip():
            message = "domain is required"
            raise RequestValidationError(message, details={"domain": message})

        normalized_domain = domain.strip()
        if len(normalized_domain) > max_domain_length:
            message = f"domain must be at most {max_domain_length} characters"
            raise RequestValidationError(message, details={"domain": message})

        return cls(domain=normalized_domain)
