from flask import Blueprint, current_app, jsonify, request

from app.extensions import limiter
from app.schemas.certificate_schema import (
    ApiException,
    CertificateResponse,
    GenerateCertificateRequest,
    PolicyValidationError,
    RequestValidationError,
)
from app.services import certificate_service
from app.utils.fqdn_validator import InvalidFQDNError

certificate_blueprint = Blueprint("certificate", __name__, url_prefix="/api/v1")


@certificate_blueprint.post("/generate")
@limiter.limit(lambda: str(current_app.config["RATE_LIMIT_PER_IP"]))
def post_generate_certificate():
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
        parsed_request = GenerateCertificateRequest.from_payload(
            payload,
            max_domain_length=int(current_app.config["MAX_DOMAIN_LENGTH"]),
        )
        service_result = certificate_service.generate_certificate(parsed_request.domain)
    except RequestValidationError as exc:
        raise ApiException(
            error="invalid_request",
            message=str(exc),
            status_code=400,
            details=exc.details,
        ) from exc
    except InvalidFQDNError as exc:
        raise ApiException(
            error="invalid_domain",
            message="Domain is invalid",
            status_code=400,
        ) from exc
    except PolicyValidationError as exc:
        raise ApiException(
            error="invalid_request",
            message="Request is invalid",
            status_code=400,
        ) from exc
    except certificate_service.CertificateGenerationError as exc:
        current_app.logger.error("Certificate generation failed")
        raise ApiException(
            error="generation_failed",
            message="Certificate generation failed",
            status_code=500,
        ) from exc
    except Exception as exc:  # pragma: no cover - covered by integration tests
        current_app.logger.error("Unhandled certificate service error")
        raise ApiException(
            error="generation_failed",
            message="Certificate generation failed",
            status_code=500,
        ) from exc

    response = CertificateResponse.from_service_result(service_result)
    return jsonify(response.__dict__), 200
