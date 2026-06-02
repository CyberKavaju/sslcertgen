from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Callable, Protocol
from uuid import uuid4

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.services import certificate_service
from app.services.certificate_bundle_service import build_certificate_bundle
from app.services.dns_challenge_service import (
    build_challenge_name,
    generate_challenge_value,
    verify_txt_record,
)
from app.utils.fqdn_validator import InvalidFQDNError, validate_fqdn

WizardStatus = str


class DNSChallengeProvider(Protocol):
    def build_challenge_name(self, domain: str) -> str:
        ...

    def generate_challenge_value(self) -> str:
        ...

    def verify_txt_record(self, challenge_name: str, expected_value: str) -> dict[str, object]:
        ...


CertificateIssuer = Callable[[str, str], dict[str, object]]


@dataclass
class WizardSession:
    internal_id: str
    domain: str
    email: str
    challenge_name: str
    challenge_value: str
    status: WizardStatus
    created_at: datetime
    updated_at: datetime
    issued_at: datetime | None = None
    artifacts: dict[str, str] | None = None
    verification_evidence: list[str] | None = None


class WizardServiceError(RuntimeError):
    def __init__(self, *, error: str, message: str, status_code: int):
        super().__init__(message)
        self.error = error
        self.message = message
        self.status_code = status_code


class WizardValidationError(WizardServiceError):
    def __init__(self, message: str):
        super().__init__(error="invalid_request", message=message, status_code=400)


class WizardInvalidSessionError(WizardServiceError):
    def __init__(self):
        super().__init__(
            error="invalid_session",
            message="Session is invalid or expired",
            status_code=401,
        )


class WizardSessionNotFoundError(WizardServiceError):
    def __init__(self):
        super().__init__(
            error="session_not_found",
            message="Wizard session was not found",
            status_code=404,
        )


class WizardConflictError(WizardServiceError):
    def __init__(self, message: str):
        super().__init__(error="txt_verification_required", message=message, status_code=409)


def _default_certificate_issuer(domain: str, _email: str) -> dict[str, object]:
    result = certificate_service.generate_certificate(domain)
    issued_at = datetime.now(UTC)
    return {
        "issued_at": issued_at,
        "artifacts": {
            "fullchain.pem": result.certificate_pem,
            "privkey.pem": result.private_key_pem,
            "cert.pem": result.certificate_pem,
        },
    }


class PublicCertWizardService:
    def __init__(
        self,
        *,
        secret_key: str,
        session_ttl_seconds: int,
        dns_service: DNSChallengeProvider | None = None,
        certificate_issuer: CertificateIssuer | None = None,
    ):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="public-cert-wizard")
        self._session_ttl_seconds = session_ttl_seconds
        self._sessions: dict[str, WizardSession] = {}
        self._lock = Lock()

        self._dns_service: DNSChallengeProvider = dns_service or self
        self._certificate_issuer: CertificateIssuer = (
            certificate_issuer or _default_certificate_issuer
        )

    # Delegated DNS interface for testability.
    def build_challenge_name(self, domain: str) -> str:
        return build_challenge_name(domain)

    def generate_challenge_value(self) -> str:
        return generate_challenge_value()

    def verify_txt_record(self, challenge_name: str, expected_value: str):
        return verify_txt_record(challenge_name, expected_value).to_dict()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _sign(self, internal_id: str) -> str:
        return self._serializer.dumps({"sid": internal_id})

    def _unsign(self, session_id: str) -> str:
        try:
            payload = self._serializer.loads(session_id, max_age=self._session_ttl_seconds)
            internal_id = payload.get("sid")
            if not isinstance(internal_id, str) or not internal_id:
                raise WizardInvalidSessionError()
            return internal_id
        except (BadSignature, SignatureExpired) as exc:
            raise WizardInvalidSessionError() from exc

    def _cleanup_expired(self) -> None:
        now = self._now()
        stale_keys = [
            key
            for key, value in self._sessions.items()
            if (now - value.updated_at).total_seconds() > self._session_ttl_seconds
        ]
        for key in stale_keys:
            self._sessions.pop(key, None)

    def _resolve_session(self, session_id: str) -> WizardSession:
        internal_id = self._unsign(session_id)

        with self._lock:
            self._cleanup_expired()
            session = self._sessions.get(internal_id)
            if session is None:
                raise WizardSessionNotFoundError()
            return session

    def start_session(self, *, domain: str, email: str | None = None) -> dict[str, object]:
        try:
            canonical_domain = validate_fqdn(domain)
        except InvalidFQDNError as exc:
            raise WizardValidationError("Domain is invalid") from exc

        normalized_email = (
            email.strip().lower() if isinstance(email, str) and email.strip() else f"admin@{canonical_domain}"
        )

        now = self._now()
        internal_id = str(uuid4())
        challenge_name = self._dns_service.build_challenge_name(canonical_domain)
        challenge_value = self._dns_service.generate_challenge_value()

        with self._lock:
            self._cleanup_expired()
            self._sessions[internal_id] = WizardSession(
                internal_id=internal_id,
                domain=canonical_domain,
                email=normalized_email,
                challenge_name=challenge_name,
                challenge_value=challenge_value,
                status="initialized",
                created_at=now,
                updated_at=now,
            )

        return {
            "session_id": self._sign(internal_id),
            "status": "initialized",
            "domain": canonical_domain,
            "email": normalized_email,
        }

    def get_txt_instructions(self, session_id: str) -> dict[str, object]:
        session = self._resolve_session(session_id)
        if session.status == "initialized":
            session.status = "txt_pending"
            session.updated_at = self._now()

        return {
            "session_id": session_id,
            "status": session.status,
            "challenge_name": session.challenge_name,
            "challenge_value": session.challenge_value,
            "domain": session.domain,
        }

    def verify_txt(self, session_id: str) -> dict[str, object]:
        session = self._resolve_session(session_id)
        verification = self._dns_service.verify_txt_record(
            challenge_name=session.challenge_name,
            expected_value=session.challenge_value,
        )

        verified = bool(verification.get("verified"))
        session.status = "txt_verified" if verified else "txt_pending"
        session.updated_at = self._now()
        raw_values = verification.get("observed_values", [])
        if not isinstance(raw_values, list):
            raw_values = []
        session.verification_evidence = [str(value) for value in raw_values]

        return {
            "session_id": session_id,
            "status": session.status,
            "verified": verified,
            "challenge_name": session.challenge_name,
            "challenge_value": session.challenge_value,
            "observed_values": session.verification_evidence,
        }

    def generate_certificate(self, session_id: str) -> dict[str, object]:
        session = self._resolve_session(session_id)
        if session.status != "txt_verified":
            raise WizardConflictError("TXT verification must pass before certificate issuance")

        session.status = "issuance_running"
        session.updated_at = self._now()

        try:
            issued = self._certificate_issuer(session.domain, session.email)
        except Exception as exc:
            session.status = "failed"
            session.updated_at = self._now()
            raise WizardServiceError(
                error="generation_failed",
                message="Certificate generation failed",
                status_code=500,
            ) from exc

        issued_at = issued.get("issued_at")
        if not isinstance(issued_at, datetime):
            issued_at = self._now()

        artifacts = issued.get("artifacts")
        if not isinstance(artifacts, dict):
            raise WizardServiceError(
                error="generation_failed",
                message="Certificate generation failed",
                status_code=500,
            )

        session.status = "issued"
        session.issued_at = issued_at
        session.artifacts = {str(key): str(value) for key, value in artifacts.items()}
        session.updated_at = self._now()

        return {
            "session_id": session_id,
            "status": session.status,
            "ready_to_download": True,
        }

    def build_download_bundle(self, session_id: str) -> tuple[str, bytes]:
        session = self._resolve_session(session_id)
        if session.status != "issued" or not session.artifacts or not session.issued_at:
            raise WizardConflictError("Certificate is not ready to download")

        archive_bytes = build_certificate_bundle(
            domain=session.domain,
            issued_at=session.issued_at,
            artifacts=session.artifacts,
        )
        return f"{session.domain}.zip", archive_bytes