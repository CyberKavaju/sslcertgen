import io
import json
import zipfile
from datetime import UTC, datetime


def _build_readme(domain: str, issued_at: datetime) -> str:
    timestamp = issued_at.astimezone(UTC).isoformat()
    return (
        "TLS Certificate Bundle\n"
        "======================\n\n"
        f"Domain: {domain}\n"
        f"Issued at (UTC): {timestamp}\n\n"
        "Included files:\n"
        "- fullchain.pem: Full certificate chain\n"
        "- privkey.pem: Private key\n"
        "- cert.pem: Leaf certificate (optional)\n"
        "- chain.pem: Intermediate chain (optional)\n"
    )


def build_certificate_bundle(
    *,
    domain: str,
    issued_at: datetime,
    artifacts: dict[str, str],
    expiry: str | None = None,
) -> bytes:
    required = {"fullchain.pem", "privkey.pem"}
    missing = sorted(required - set(artifacts.keys()))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing required artifact(s): {missing_text}")

    metadata = {
        "domain": domain,
        "issued_at": issued_at.astimezone(UTC).isoformat(),
    }
    if expiry:
        metadata["expiry"] = expiry

    with io.BytesIO() as memory_buffer:
        with zipfile.ZipFile(memory_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("fullchain.pem", artifacts["fullchain.pem"])
            archive.writestr("privkey.pem", artifacts["privkey.pem"])

            if "cert.pem" in artifacts:
                archive.writestr("cert.pem", artifacts["cert.pem"])
            if "chain.pem" in artifacts:
                archive.writestr("chain.pem", artifacts["chain.pem"])

            archive.writestr("README.txt", _build_readme(domain, issued_at))
            archive.writestr("metadata.json", json.dumps(metadata, indent=2, sort_keys=True))

        return memory_buffer.getvalue()