import pytest

from app.config import CONFIG_BY_NAME


@pytest.mark.unit
def test_config_mapping_has_expected_profiles() -> None:
    assert set(CONFIG_BY_NAME.keys()) == {"development", "testing", "production"}


@pytest.mark.unit
def test_testing_config_enables_testing_mode() -> None:
    testing = CONFIG_BY_NAME["testing"]

    assert testing.TESTING is True


@pytest.mark.unit
def test_rate_limit_value_can_be_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_PER_IP", "20/minute")

    development = CONFIG_BY_NAME["development"]

    assert development.rate_limit_per_ip() == "20/minute"


@pytest.mark.unit
def test_proxy_fix_hops_default_to_one(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRUST_PROXY_HOPS", raising=False)

    production = CONFIG_BY_NAME["production"]

    assert production.trust_proxy_hops() == 1


@pytest.mark.unit
def test_max_content_length_default_is_8192(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAX_CONTENT_LENGTH", raising=False)

    development = CONFIG_BY_NAME["development"]

    assert development.max_content_length() == 8192


@pytest.mark.unit
def test_max_domain_length_default_is_253(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAX_DOMAIN_LENGTH", raising=False)

    production = CONFIG_BY_NAME["production"]

    assert production.max_domain_length() == 253


@pytest.mark.unit
def test_security_headers_toggle_can_be_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "false")

    testing = CONFIG_BY_NAME["testing"]

    assert testing.security_headers_enabled() is False


@pytest.mark.unit
def test_https_enforcement_toggle_defaults_to_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HTTPS_ENFORCEMENT_ENABLED", raising=False)

    development = CONFIG_BY_NAME["development"]

    assert development.https_enforcement_enabled() is False


@pytest.mark.unit
def test_hsts_toggle_defaults_to_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HSTS_ENABLED", raising=False)

    production = CONFIG_BY_NAME["production"]

    assert production.hsts_enabled() is False
