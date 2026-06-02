import secrets
from dataclasses import dataclass
from typing import Protocol

import dns.exception
import dns.resolver


@dataclass(frozen=True)
class DNSVerificationResult:
    verified: bool
    challenge_name: str
    expected_value: str
    observed_values: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "verified": self.verified,
            "challenge_name": self.challenge_name,
            "expected_value": self.expected_value,
            "observed_values": self.observed_values,
        }


class DNSResolver(Protocol):
    def resolve(self, name: str, record_type: str):
        ...


def build_challenge_name(domain: str) -> str:
    return f"_acme-challenge.{domain}"


def generate_challenge_value() -> str:
    return secrets.token_urlsafe(24)


def _decode_txt_answer(answer: object) -> str:
    chunks = []
    raw_parts = getattr(answer, "strings", ())
    for part in raw_parts:
        if isinstance(part, bytes):
            chunks.append(part.decode("utf-8", errors="ignore"))
        else:
            chunks.append(str(part))
    return "".join(chunks).strip().strip('"')


def verify_txt_record(
    challenge_name: str,
    expected_value: str,
    *,
    resolver: DNSResolver | None = None,
) -> DNSVerificationResult:
    active_resolver = resolver if resolver is not None else dns.resolver.Resolver()

    observed_values: list[str] = []
    try:
        answers = active_resolver.resolve(challenge_name, "TXT")
        for answer in answers:
            value = _decode_txt_answer(answer)
            if value:
                observed_values.append(value)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        observed_values = []
    except dns.exception.DNSException:
        observed_values = []

    verified = expected_value in observed_values
    return DNSVerificationResult(
        verified=verified,
        challenge_name=challenge_name,
        expected_value=expected_value,
        observed_values=observed_values,
    )