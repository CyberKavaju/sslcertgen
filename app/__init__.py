import os
from io import BytesIO

from flask import Flask, jsonify, request
from flask_limiter.errors import RateLimitExceeded
from werkzeug.exceptions import MethodNotAllowed, NotFound, RequestEntityTooLarge

from app.config import CONFIG_BY_NAME
from app.extensions import init_extensions
from app.schemas.certificate_schema import ApiErrorResponse, ApiException


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, template_folder="views", static_folder="static")

    selected_config = config_name
    if selected_config is None:
        selected_config = os.getenv("FLASK_CONFIG") or "development"

    config_class = CONFIG_BY_NAME.get(selected_config, CONFIG_BY_NAME["development"])
    app.config.from_object(config_class)

    app.config["RATE_LIMIT_PER_IP"] = config_class.rate_limit_per_ip()
    app.config["MAX_CONTENT_LENGTH"] = config_class.max_content_length()
    app.config["MAX_DOMAIN_LENGTH"] = config_class.max_domain_length()
    app.config["TRUST_PROXY_HOPS"] = config_class.trust_proxy_hops()

    app.config["RATELIMIT_ENABLED"] = True
    app.config["RATELIMIT_STORAGE_URI"] = config_class.limiter_storage_uri()
    app.config["SECRET_KEY"] = config_class.secret_key()
    app.config["HTTPS_ENFORCEMENT_ENABLED"] = config_class.https_enforcement_enabled()
    app.config["SECURITY_HEADERS_ENABLED"] = config_class.security_headers_enabled()
    app.config["HSTS_ENABLED"] = config_class.hsts_enabled()
    app.config["HSTS_MAX_AGE"] = config_class.hsts_max_age()
    app.config["HSTS_INCLUDE_SUBDOMAINS"] = config_class.hsts_include_subdomains()
    app.config["HSTS_PRELOAD"] = config_class.hsts_preload()
    app.config["CONTENT_SECURITY_POLICY"] = config_class.content_security_policy()
    app.config["WIZARD_SESSION_TTL_SECONDS"] = config_class.wizard_session_ttl_seconds()
    app.config["WIZARD_SESSION_SECRET"] = config_class.wizard_session_secret()
    app.config["WIZARD_START_RATE_LIMIT"] = config_class.wizard_start_rate_limit()
    app.config["WIZARD_VERIFY_RATE_LIMIT"] = config_class.wizard_verify_rate_limit()
    app.config["WIZARD_GENERATE_RATE_LIMIT"] = config_class.wizard_generate_rate_limit()

    init_extensions(app)

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"}), 200

    @app.before_request
    def enforce_request_size_limits():
        if request.method not in {"POST", "PUT", "PATCH"}:
            return

        max_content_length = int(app.config["MAX_CONTENT_LENGTH"])
        if request.content_length is not None and request.content_length > max_content_length:
            raise RequestEntityTooLarge()

        transfer_encoding = request.headers.get("Transfer-Encoding", "")
        has_chunked_transfer = "chunked" in transfer_encoding.lower()
        should_guard_stream = request.content_length is None or has_chunked_transfer
        if not should_guard_stream:
            return

        input_stream = request.environ.get("wsgi.input")
        if input_stream is None:
            return

        body = input_stream.read(max_content_length + 1)
        if len(body) > max_content_length:
            raise RequestEntityTooLarge()

        request.environ["wsgi.input"] = BytesIO(body)

    @app.before_request
    def enforce_https_if_configured():
        if app.config["HTTPS_ENFORCEMENT_ENABLED"] and not request.is_secure:
            payload = ApiErrorResponse(error="https_required", message="HTTPS is required")
            return jsonify(payload.to_dict()), 400

        return None

    @app.after_request
    def apply_security_headers(response):
        if not app.config["SECURITY_HEADERS_ENABLED"]:
            return response

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = app.config["CONTENT_SECURITY_POLICY"]

        if app.config["HSTS_ENABLED"] and request.is_secure:
            hsts_header = f"max-age={int(app.config['HSTS_MAX_AGE'])}"
            if app.config["HSTS_INCLUDE_SUBDOMAINS"]:
                hsts_header += "; includeSubDomains"
            if app.config["HSTS_PRELOAD"]:
                hsts_header += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_header

        return response

    @app.errorhandler(ApiException)
    def handle_api_exception(exc: ApiException):
        payload = ApiErrorResponse(
            error=exc.error,
            message=exc.message,
            details=exc.details,
        )
        return jsonify(payload.to_dict()), exc.status_code

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_error(_exc: RateLimitExceeded):
        payload = ApiErrorResponse(error="rate_limited", message="Too many requests")
        return jsonify(payload.to_dict()), 429

    @app.errorhandler(RequestEntityTooLarge)
    def handle_payload_too_large(_exc: RequestEntityTooLarge):
        payload = ApiErrorResponse(
            error="payload_too_large",
            message="Request payload is too large",
        )
        return jsonify(payload.to_dict()), 413

    @app.errorhandler(NotFound)
    def handle_not_found(_exc: NotFound):
        payload = ApiErrorResponse(error="not_found", message="Resource not found")
        return jsonify(payload.to_dict()), 404

    @app.errorhandler(MethodNotAllowed)
    def handle_method_not_allowed(_exc: MethodNotAllowed):
        payload = ApiErrorResponse(error="method_not_allowed", message="Method not allowed")
        return jsonify(payload.to_dict()), 405

    @app.errorhandler(Exception)
    def handle_unexpected_exception(_exc: Exception):
        app.logger.error("Unhandled server error")
        payload = ApiErrorResponse(
            error="generation_failed",
            message="Certificate generation failed",
        )
        return jsonify(payload.to_dict()), 500

    return app
