from flask import Blueprint, render_template


ui_blueprint = Blueprint("ui", __name__)


@ui_blueprint.get("/")
def get_certificate_page():
    return render_template("certificate/index.html")