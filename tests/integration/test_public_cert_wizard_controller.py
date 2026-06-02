import io
import zipfile

import pytest

from app.services.public_cert_wizard_service import PublicCertWizardService


@pytest.fixture()
def wizard_service(app, monkeypatch: pytest.MonkeyPatch):
    class _FakeDNSService:
        def __init__(self):
            self.verified = False

        def build_challenge_name(self, domain: str) -> str:
            return f"_acme-challenge.{domain}"

        def generate_challenge_value(self) -> str:
            return "challenge-token"

        def verify_txt_record(self, challenge_name: str, expected_value: str):
            observed = [expected_value] if self.verified else ["wrong-value"]
            return {
                "verified": self.verified,
                "challenge_name": challenge_name,
                "expected_value": expected_value,
                "observed_values": observed,
            }

    class _FakeIssuer:
        def __call__(self, domain: str, _email: str):
            return {
                "artifacts": {
                    "fullchain.pem": f"FULLCHAIN-{domain}",
                    "privkey.pem": "PRIVKEY",
                    "cert.pem": "CERT",
                    "chain.pem": "CHAIN",
                }
            }

    service = PublicCertWizardService(
        secret_key="test-secret",
        dns_service=_FakeDNSService(),
        certificate_issuer=_FakeIssuer(),
        session_ttl_seconds=3600,
    )
    app.config["PUBLIC_CERT_WIZARD_SERVICE"] = service
    monkeypatch.setitem(app.config, "WIZARD_START_RATE_LIMIT", "100/minute")
    monkeypatch.setitem(app.config, "WIZARD_VERIFY_RATE_LIMIT", "100/minute")
    monkeypatch.setitem(app.config, "WIZARD_GENERATE_RATE_LIMIT", "100/minute")
    return service


@pytest.mark.integration
def test_wizard_happy_path_returns_downloadable_zip(client, wizard_service) -> None:
    started = client.post(
        "/api/v1/public-cert/wizard/start",
        json={"domain": "example.com"},
    )

    assert started.status_code == 201
    start_payload = started.get_json()
    assert start_payload is not None
    session_id = start_payload["session_id"]

    txt = client.get(f"/api/v1/public-cert/wizard/{session_id}/txt")
    assert txt.status_code == 200

    wizard_service._dns_service.verified = True
    verify = client.post(f"/api/v1/public-cert/wizard/{session_id}/verify-txt")
    assert verify.status_code == 200
    assert verify.get_json()["verified"] is True

    generate = client.post(f"/api/v1/public-cert/wizard/{session_id}/generate")
    assert generate.status_code == 200
    assert generate.get_json()["status"] == "issued"

    download = client.get(f"/api/v1/public-cert/wizard/{session_id}/download.zip")
    assert download.status_code == 200
    assert download.mimetype == "application/zip"

    archive = zipfile.ZipFile(io.BytesIO(download.data), mode="r")
    names = sorted(archive.namelist())
    assert "fullchain.pem" in names
    assert "privkey.pem" in names
    assert "README.txt" in names


@pytest.mark.integration
def test_wizard_generate_returns_409_when_txt_not_verified(client, wizard_service) -> None:
    started = client.post(
        "/api/v1/public-cert/wizard/start",
        json={"domain": "example.com"},
    )
    session_id = started.get_json()["session_id"]

    response = client.post(f"/api/v1/public-cert/wizard/{session_id}/generate")

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "txt_verification_required",
        "message": "TXT verification must pass before certificate issuance",
    }


@pytest.mark.integration
def test_wizard_verify_keeps_pending_status_on_mismatch(client, wizard_service) -> None:
    started = client.post(
        "/api/v1/public-cert/wizard/start",
        json={"domain": "example.com"},
    )
    session_id = started.get_json()["session_id"]

    verify = client.post(f"/api/v1/public-cert/wizard/{session_id}/verify-txt")

    assert verify.status_code == 200
    assert verify.get_json()["verified"] is False
    assert verify.get_json()["status"] == "txt_pending"


@pytest.mark.integration
def test_wizard_invalid_session_returns_401(client) -> None:
    response = client.get("/api/v1/public-cert/wizard/not-a-valid-session/txt")

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "invalid_session",
        "message": "Session is invalid or expired",
    }