import pytest


@pytest.mark.integration
def test_root_route_renders_certificate_page(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"

    html = response.get_data(as_text=True)

    assert 'id="wizard-start-form"' in html
    assert 'name="domain"' in html
    assert 'id="wizard-start-button"' in html
    assert 'id="verify-txt-button"' in html
    assert 'id="wizard-generate-button"' in html
    assert 'id="wizard-download-button"' in html
    assert 'id="validation-message"' in html
    assert 'id="api-error-message"' in html
    assert 'id="challenge-name"' in html
    assert 'id="challenge-value"' in html
    assert 'id="resolver-evidence"' in html


@pytest.mark.integration
def test_root_route_includes_page_assets_and_state_hooks(client) -> None:
    response = client.get("/")

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'https://cdn.tailwindcss.com?plugins=forms,container-queries' in html
    assert 'fonts.googleapis.com/css2?family=Inter' in html
    assert 'fonts.googleapis.com/css2?family=Material+Symbols+Outlined' in html
    assert 'href="/static/css/certificate_page.css"' in html
    assert 'src="/static/js/certificate_page.js"' in html
    assert 'data-step-marker="1"' in html
    assert 'data-step-marker="4"' in html