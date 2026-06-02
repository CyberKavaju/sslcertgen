import pytest

from app.services.dns_challenge_service import (
    DNSVerificationResult,
    build_challenge_name,
    verify_txt_record,
)


class _FakeAnswer:
    def __init__(self, text: str):
        self.strings = (text.encode("utf-8"),)


class _FakeResolver:
    def __init__(self, records: list[str]):
        self._records = records

    def resolve(self, _name: str, _record_type: str):
        return [_FakeAnswer(value) for value in self._records]


@pytest.mark.unit
def test_build_challenge_name_returns_expected_prefix() -> None:
    assert build_challenge_name("example.com") == "_acme-challenge.example.com"


@pytest.mark.unit
def test_verify_txt_record_returns_verified_when_expected_value_present() -> None:
    resolver = _FakeResolver(records=["mismatch", "expected-token"])

    result = verify_txt_record(
        challenge_name="_acme-challenge.example.com",
        expected_value="expected-token",
        resolver=resolver,
    )

    assert isinstance(result, DNSVerificationResult)
    assert result.verified is True
    assert "expected-token" in result.observed_values


@pytest.mark.unit
def test_verify_txt_record_returns_unverified_when_expected_value_missing() -> None:
    resolver = _FakeResolver(records=["other-value"])

    result = verify_txt_record(
        challenge_name="_acme-challenge.example.com",
        expected_value="expected-token",
        resolver=resolver,
    )

    assert result.verified is False
    assert result.observed_values == ["other-value"]