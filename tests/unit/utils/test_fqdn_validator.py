import pytest

from app.utils.fqdn_validator import InvalidFQDNError, normalize_fqdn, validate_fqdn


@pytest.mark.unit
@pytest.mark.parametrize(
    "raw_domain, expected",
    [
        ("example.com", "example.com"),
        ("EXAMPLE.COM.", "example.com"),
        ("sub.example.com", "sub.example.com"),
        ("xn--bcher-kva.example", "xn--bcher-kva.example"),
    ],
)
def test_validate_fqdn_accepts_valid_ascii_and_punycode(raw_domain: str, expected: str) -> None:
    assert validate_fqdn(raw_domain) == expected


@pytest.mark.unit
def test_normalize_fqdn_strips_and_removes_trailing_dot() -> None:
    assert normalize_fqdn("  Example.COM.  ") == "example.com"


@pytest.mark.unit
@pytest.mark.parametrize(
    "raw_domain",
    [
        "",
        "localhost",
        "*.example.com",
        "bad domain.com",
        "-bad.example.com",
        "bad-.example.com",
        "example..com",
        "127.0.0.1",
        "xn--.example",
    ],
)
def test_validate_fqdn_rejects_invalid_inputs(raw_domain: str) -> None:
    with pytest.raises(InvalidFQDNError):
        validate_fqdn(raw_domain)


@pytest.mark.unit
def test_validate_fqdn_rejects_unicode_input() -> None:
    with pytest.raises(InvalidFQDNError):
        validate_fqdn("münchen.de")


@pytest.mark.unit
def test_validate_fqdn_uses_sanitized_error_message() -> None:
    raw = "bad domain.com"

    with pytest.raises(InvalidFQDNError) as exc_info:
        validate_fqdn(raw)

    message = str(exc_info.value)
    assert message.startswith("Invalid FQDN: ")
    assert raw not in message
