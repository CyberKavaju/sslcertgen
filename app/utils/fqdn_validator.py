import re
from ipaddress import ip_address

import idna


_FQDN_LABEL_RE = re.compile(r"^[a-z0-9-]{1,63}$")


class InvalidFQDNError(ValueError):
    """Raised when a provided domain is not a valid strict FQDN."""


def _invalid(reason: str) -> InvalidFQDNError:
    return InvalidFQDNError(f"Invalid FQDN: {reason}")


def normalize_fqdn(domain: str) -> str:
    """Normalize a domain to its canonical ASCII form for validation and cert usage."""
    return domain.strip().lower().rstrip(".")


def _validate_punycode_label(label: str) -> None:
    if not label.startswith("xn--"):
        return

    try:
        idna.decode(label)
    except idna.IDNAError as exc:
        raise _invalid("invalid punycode label") from exc


def validate_fqdn(domain: str) -> str:
    """Validate a strict FQDN and return its canonical ASCII form."""
    if not isinstance(domain, str):
        raise _invalid("domain must be a string")

    normalized = normalize_fqdn(domain)
    if not normalized:
        raise _invalid("domain is empty")

    if not normalized.isascii():
        raise _invalid("domain must be ASCII")

    if "*" in normalized:
        raise _invalid("wildcards are not allowed")

    if len(normalized) > 253:
        raise _invalid("domain exceeds 253 characters")

    labels = normalized.split(".")
    if len(labels) < 2:
        raise _invalid("domain must include at least one dot")

    if any(label == "" for label in labels):
        raise _invalid("domain labels cannot be empty")

    try:
        ip_address(normalized)
    except ValueError:
        pass
    else:
        raise _invalid("IP addresses are not allowed")

    for label in labels:
        if not _FQDN_LABEL_RE.fullmatch(label):
            raise _invalid("domain label contains invalid characters")

        if label.startswith("-") or label.endswith("-"):
            raise _invalid("domain labels cannot start or end with hyphen")

        _validate_punycode_label(label)

    if labels[-1].isdigit():
        raise _invalid("top-level domain cannot be numeric")

    return normalized
