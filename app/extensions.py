from flask import Flask, request
from flask_limiter import Limiter
from werkzeug.middleware.proxy_fix import ProxyFix

from app.services.public_cert_wizard_service import PublicCertWizardService


def _rate_limit_key() -> str:
    if request.access_route:
        return request.access_route[0]
    if request.remote_addr:
        return request.remote_addr
    return "unknown"


limiter = Limiter(key_func=_rate_limit_key)


def init_extensions(app: Flask) -> None:
    from app.controllers.certificate_controller import certificate_blueprint
    from app.controllers.public_cert_wizard_controller import public_cert_wizard_blueprint
    from app.controllers.ui_controller import ui_blueprint

    setattr(app, "wsgi_app", ProxyFix(app.wsgi_app, x_for=app.config["TRUST_PROXY_HOPS"]))
    limiter.init_app(app)
    app.config["PUBLIC_CERT_WIZARD_SERVICE"] = PublicCertWizardService(
        secret_key=str(app.config["WIZARD_SESSION_SECRET"]),
        session_ttl_seconds=int(app.config["WIZARD_SESSION_TTL_SECONDS"]),
    )
    app.register_blueprint(ui_blueprint)
    app.register_blueprint(certificate_blueprint)
    app.register_blueprint(public_cert_wizard_blueprint)
