from io import BytesIO
from typing import cast

from flask import Blueprint, current_app, jsonify, request, send_file

from app.extensions import limiter
from app.schemas.certificate_schema import ApiException, RequestValidationError
from app.schemas.public_cert_wizard_schema import WizardStartRequest
from app.services.public_cert_wizard_service import PublicCertWizardService, WizardServiceError

public_cert_wizard_blueprint = Blueprint(
    "public_cert_wizard",
    __name__,
    url_prefix="/api/v1/public-cert/wizard",
)


def _wizard_service():
    return cast(
        PublicCertWizardService,
        current_app.config["PUBLIC_CERT_WIZARD_SERVICE"],
    )


@public_cert_wizard_blueprint.post("/start")
@limiter.limit(lambda: str(current_app.config["WIZARD_START_RATE_LIMIT"]))
def post_start_public_cert_wizard():
    if not request.is_json:
        raise ApiException(
            error="invalid_request",
            message="Request body must be valid JSON",
            status_code=400,
        )

    payload = request.get_json(silent=True)
    if payload is None:
        raise ApiException(
            error="invalid_request",
            message="Request body must be valid JSON",
            status_code=400,
        )

    try:
        parsed_request = WizardStartRequest.from_payload(
            payload,
            max_domain_length=int(current_app.config["MAX_DOMAIN_LENGTH"]),
        )
        result = _wizard_service().start_session(
            domain=parsed_request.domain,
        )
    except RequestValidationError as exc:
        raise ApiException(
            error="invalid_request",
            message=str(exc),
            status_code=400,
            details=exc.details,
        ) from exc
    except WizardServiceError as exc:
        raise ApiException(error=exc.error, message=exc.message, status_code=exc.status_code) from exc

    return jsonify(result), 201


@public_cert_wizard_blueprint.get("/<session_id>/txt")
def get_public_cert_wizard_txt_instructions(session_id: str):
    try:
        result = _wizard_service().get_txt_instructions(session_id)
    except WizardServiceError as exc:
        raise ApiException(error=exc.error, message=exc.message, status_code=exc.status_code) from exc

    return jsonify(result), 200


@public_cert_wizard_blueprint.post("/<session_id>/verify-txt")
@limiter.limit(lambda: str(current_app.config["WIZARD_VERIFY_RATE_LIMIT"]))
def post_public_cert_wizard_verify_txt(session_id: str):
    try:
        result = _wizard_service().verify_txt(session_id)
    except WizardServiceError as exc:
        raise ApiException(error=exc.error, message=exc.message, status_code=exc.status_code) from exc

    return jsonify(result), 200


@public_cert_wizard_blueprint.post("/<session_id>/generate")
@limiter.limit(lambda: str(current_app.config["WIZARD_GENERATE_RATE_LIMIT"]))
def post_public_cert_wizard_generate(session_id: str):
    try:
        result = _wizard_service().generate_certificate(session_id)
    except WizardServiceError as exc:
        raise ApiException(error=exc.error, message=exc.message, status_code=exc.status_code) from exc

    return jsonify(result), 200


@public_cert_wizard_blueprint.get("/<session_id>/download.zip")
def get_public_cert_wizard_download_bundle(session_id: str):
    try:
        archive_name, archive_bytes = _wizard_service().build_download_bundle(session_id)
    except WizardServiceError as exc:
        raise ApiException(error=exc.error, message=exc.message, status_code=exc.status_code) from exc

    return send_file(
        path_or_file=BytesIO(archive_bytes),
        mimetype="application/zip",
        as_attachment=True,
        download_name=archive_name,
        max_age=0,
    )