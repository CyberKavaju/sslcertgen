# TLS Certificate Generator

TLS Certificate Generator is a Flask application for generating TLS certificate artifacts from a simple web UI or JSON API. The project currently supports direct self-signed certificate generation and a guided DNS TXT verification wizard that produces a downloadable certificate bundle.

The app is packaged for local Docker-based development behind Nginx and includes unit and integration tests for the Flask app, schemas, services, and validators.

## Features

- Server-rendered UI at `/` for the certificate workflow.
- JSON API for self-signed certificate generation at `/api/v1/generate`.
- Guided DNS TXT verification flow under `/api/v1/public-cert/wizard`.
- Downloadable ZIP bundle after successful wizard issuance.
- Request size limits, rate limiting, and baseline security headers.
- Docker-based local environment with HTTP and HTTPS entry points.
- Ruff, mypy, and pytest-based quality checks.

## Tech Stack

- Python 3.12
- Flask
- Gunicorn
- cryptography
- Flask-Limiter
- Docker Compose with Nginx in front of the app

## Project Layout

```text
app/           Flask application code
deployment/    Docker Compose, Nginx, and deployment scripts
docs/          Product and planning docs
tests/         Unit, integration, and E2E test suites
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- `just` for the convenience commands in the root `justfile`
- Ports `80` and `443` available on the host

### Start Locally

```bash
just start
```

This runs the local Docker stack from `deployment/docker-compose.yml` and exposes:

- `http://127.0.0.1`
- `https://127.0.0.1`

If startup fails immediately, check whether another process is already listening on ports `80` or `443`.

### Stop The Stack

```bash
just stop
```

## Local Quality Commands

Install the Python dependencies if you want to run checks outside Docker:

```bash
just install
```

Available commands:

```bash
just start
just lint
just format-check
just type-check
just test
just check-all
just stop
```

`just test` runs unit and integration tests with branch coverage and enforces a minimum coverage threshold of 60%.

## Application Endpoints

### UI

- `GET /` renders the certificate workflow page.

### Health

- `GET /healthz` returns `200` with `{"status": "ok"}`.

### Certificate API

- `POST /api/v1/generate`

Example request:

```json
{
  "domain": "example.com"
}
```

Example success response:

```json
{
  "certificate_pem": "-----BEGIN CERTIFICATE-----...",
  "private_key_pem": "-----BEGIN PRIVATE KEY-----..."
}
```

### Public Certificate Wizard API

- `POST /api/v1/public-cert/wizard/start`
- `GET /api/v1/public-cert/wizard/<session_id>/txt`
- `POST /api/v1/public-cert/wizard/<session_id>/verify-txt`
- `POST /api/v1/public-cert/wizard/<session_id>/generate`
- `GET /api/v1/public-cert/wizard/<session_id>/download.zip`

The wizard flow is:

1. Start a session for a domain.
2. Fetch the TXT challenge instructions.
3. Publish the requested DNS TXT record.
4. Verify the TXT record.
5. Generate and download the certificate bundle.

## Configuration

Key environment variables exposed by `app.config`:

| Variable | Default | Purpose |
|---|---|---|
| `FLASK_CONFIG` | `development` | Selects the Flask config profile. |
| `SECRET_KEY` | `dev-insecure-change-me` | Flask secret key. |
| `RATE_LIMIT_PER_IP` | `10/minute` | Rate limit for `/api/v1/generate`. |
| `RATELIMIT_STORAGE_URI` | `memory://` | Backend used by Flask-Limiter. |
| `MAX_CONTENT_LENGTH` | `8192` | Max request body size in bytes. |
| `MAX_DOMAIN_LENGTH` | `253` | Max accepted FQDN length. |
| `HTTPS_ENFORCEMENT_ENABLED` | `false` | Reject non-HTTPS requests when enabled. |
| `SECURITY_HEADERS_ENABLED` | `true` | Adds the app's security response headers. |
| `HSTS_ENABLED` | `false` | Enables HSTS on secure requests. |
| `WIZARD_SESSION_TTL_SECONDS` | `1800` | Public wizard session lifetime. |
| `WIZARD_START_RATE_LIMIT` | `10/minute` | Rate limit for wizard session creation. |
| `WIZARD_VERIFY_RATE_LIMIT` | `30/minute` | Rate limit for TXT verification requests. |
| `WIZARD_GENERATE_RATE_LIMIT` | `5/minute` | Rate limit for wizard certificate generation. |

## Deployment Notes

- The runtime container serves the Flask app with Gunicorn on port `8000`.
- The local Compose stack places Nginx in front of the app and binds host ports `80` and `443`.
- Production-oriented Compose and certificate helper scripts live under `deployment/`.

## Current Scope

- The direct certificate service generates self-signed certificates.
- The guided wizard performs DNS TXT verification before issuing a downloadable bundle.
- The repository already includes a path for future production deployment helpers, but the current Flask certificate service is self-signed.
