import io
import json
import zipfile
from datetime import UTC, datetime

import pytest

from app.services.certificate_bundle_service import build_certificate_bundle


@pytest.mark.unit
def test_build_certificate_bundle_contains_required_files() -> None:
    bundle = build_certificate_bundle(
        domain="example.com",
        issued_at=datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        artifacts={
            "fullchain.pem": "FULLCHAIN",
            "privkey.pem": "PRIVKEY",
            "cert.pem": "CERT",
            "chain.pem": "CHAIN",
        },
    )

    with zipfile.ZipFile(io.BytesIO(bundle), mode="r") as archive:
        names = sorted(archive.namelist())
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))

    assert names == [
        "README.txt",
        "cert.pem",
        "chain.pem",
        "fullchain.pem",
        "metadata.json",
        "privkey.pem",
    ]
    assert metadata["domain"] == "example.com"
    assert metadata["issued_at"] == "2026-01-15T12:00:00+00:00"


@pytest.mark.unit
def test_build_certificate_bundle_skips_optional_pem_files_when_missing() -> None:
    bundle = build_certificate_bundle(
        domain="example.com",
        issued_at=datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        artifacts={
            "fullchain.pem": "FULLCHAIN",
            "privkey.pem": "PRIVKEY",
        },
    )

    with zipfile.ZipFile(io.BytesIO(bundle), mode="r") as archive:
        names = sorted(archive.namelist())

    assert names == ["README.txt", "fullchain.pem", "metadata.json", "privkey.pem"]