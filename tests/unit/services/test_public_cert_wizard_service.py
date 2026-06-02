from datetime import UTC, datetime

import pytest

from app.services.public_cert_wizard_service import (
    PublicCertWizardService,
    WizardConflictError,
    WizardInvalidSessionError,
)


class _FakeDNSService:
    def __init__(self):
        self._verified = False

    def build_challenge_name(self, domain: str) -> str:
        return f"_acme-challenge.{domain}"

    def generate_challenge_value(self) -> str:
        return "challenge-token"

    def verify_txt_record(self, challenge_name: str, expected_value: str):
        return {
            "verified": self._verified,
            "challenge_name": challenge_name,
            "expected_value": expected_value,
            "observed_values": [expected_value] if self._verified else ["wrong"],
        }


class _FakeIssuer:
    def __call__(self, domain: str, email: str):
        now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        return {
            "issued_at": now,
            "artifacts": {
                "fullchain.pem": f"FULLCHAIN-{domain}",
                "privkey.pem": f"PRIVKEY-{email}",
                "cert.pem": "CERT",
            },
        }


@pytest.mark.unit
def test_start_and_get_txt_instructions_returns_pending_state() -> None:
    service = PublicCertWizardService(
        secret_key="test-secret",
        dns_service=_FakeDNSService(),
        certificate_issuer=_FakeIssuer(),
        session_ttl_seconds=600,
    )

    started = service.start_session(domain="example.com", email="admin@example.com")
    txt_info = service.get_txt_instructions(started["session_id"])

    assert txt_info["status"] == "txt_pending"
    assert txt_info["challenge_name"] == "_acme-challenge.example.com"
    assert txt_info["challenge_value"] == "challenge-token"


@pytest.mark.unit
def test_generate_requires_verified_txt_precondition() -> None:
    service = PublicCertWizardService(
        secret_key="test-secret",
        dns_service=_FakeDNSService(),
        certificate_issuer=_FakeIssuer(),
        session_ttl_seconds=600,
    )

    started = service.start_session(domain="example.com", email="admin@example.com")

    with pytest.raises(WizardConflictError):
        service.generate_certificate(started["session_id"])


@pytest.mark.unit
def test_verify_then_generate_updates_status_to_issued() -> None:
    dns_service = _FakeDNSService()
    service = PublicCertWizardService(
        secret_key="test-secret",
        dns_service=dns_service,
        certificate_issuer=_FakeIssuer(),
        session_ttl_seconds=600,
    )

    started = service.start_session(domain="example.com", email="admin@example.com")
    dns_service._verified = True

    verification = service.verify_txt(started["session_id"])
    generated = service.generate_certificate(started["session_id"])

    assert verification["verified"] is True
    assert generated["status"] == "issued"
    assert generated["ready_to_download"] is True


@pytest.mark.unit
def test_invalid_signed_session_id_raises_invalid_session_error() -> None:
    service = PublicCertWizardService(
        secret_key="test-secret",
        dns_service=_FakeDNSService(),
        certificate_issuer=_FakeIssuer(),
        session_ttl_seconds=600,
    )

    with pytest.raises(WizardInvalidSessionError):
        service.get_txt_instructions("not-a-valid-session")