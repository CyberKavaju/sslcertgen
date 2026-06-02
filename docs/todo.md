# TLS Cert Generator - Dependency-Ordered Development Todo

This file lists tasks in strict sequence based on dependencies. Complete tasks top-to-bottom.

## Phase 0 - Project Foundation

- [x] 0.1 Confirm scope and defaults from PRD
  - Outputs: final decisions for framework (`FastAPI` or `Flask`), cert mode (self-signed first), and deployment target.
  - Notes: Flask + self-signed MVP + single-container-behind-proxy defaults recorded in `docs/prd.md`.
  - Depends on: none
- [x] 0.2 Initialize repository layout
  - Outputs: baseline folders for app code, tests, docs, and deployment artifacts.
  - Notes: scaffold created under `app/`, `tests/`, and `deployment/`.
  - Depends on: 0.1
- [x] 0.3 Create Python environment and dependency manifests
  - Outputs: pinned dependencies for runtime and dev/test tools.
  - Notes: `requirements.txt`, `requirements-dev.txt`, and baseline `pyproject.toml` added.
  - Depends on: 0.2
- [x] 0.4 Define environment configuration contract
  - Outputs: required env vars (rate limits, app mode, logging level, TLS/proxy settings).
  - Notes: `.env.example`, `app/config.py`, and app factory config loading added.
  - Depends on: 0.3
- [x] 0.5 Add quality gates and local automation
  - Outputs: lint/format/type/test commands and a single local entrypoint for checks.
  - Notes: `justfile` added with `check-all`; tests and markers configured.
  - Depends on: 0.3

## Phase 1 - Core Domain Logic

- [ ] 1.1 Implement strict FQDN/domain validator
  - Outputs: reusable validation module with edge-case coverage.
  - Depends on: 0.5
- [ ] 1.2 Implement certificate/key generation service using `cryptography`
  - Outputs: in-memory keypair + X.509 cert generation for a valid domain.
  - Depends on: 1.1
- [ ] 1.3 Add certificate generation policy options
  - Outputs: configurable parameters (key size/algorithm, validity period, subject/SAN rules).
  - Depends on: 1.2
- [ ] 1.4 Implement secure output shaping
  - Outputs: response DTOs that include cert/key PEM and exclude sensitive debug details.
  - Depends on: 1.2
- [ ] 1.5 Add unit tests for domain + cert modules
  - Outputs: tests asserting validity checks, subject/SAN correctness, and PEM format.
  - Depends on: 1.1, 1.2, 1.3, 1.4

## Phase 2 - API Layer

- [x] 2.1 Create application factory and API routing skeleton
  - Outputs: bootstrapped app with route registration and startup wiring.
  - Depends on: 1.5
- [x] 2.2 Implement `POST /generate`
  - Outputs: validated request handling, service invocation, structured success/error responses.
  - Depends on: 2.1, 1.4
- [x] 2.3 Implement `GET /healthz`
  - Outputs: health endpoint for probes.
  - Depends on: 2.1
- [x] 2.4 Add API error model and status mapping
  - Outputs: consistent 400/429/500 error contract.
  - Depends on: 2.2
- [x] 2.5 Add API integration tests
  - Outputs: endpoint tests for valid domain, invalid domain, and failure cases.
  - Depends on: 2.2, 2.3, 2.4

## Phase 3 - Security and Abuse Protection

- [x] 3.1 Add per-IP rate limiting
  - Outputs: throttling policy and 429 responses.
  - Depends on: 2.2
- [x] 3.2 Harden input boundaries and request limits
  - Outputs: max payload size, domain length limits, and rejected malformed payloads.
  - Depends on: 2.2
- [x] 3.3 Prevent sensitive data leakage
  - Outputs: guardrails ensuring private keys are never logged or persisted.
  - Depends on: 2.2
- [x] 3.4 Add TLS/proxy trust and security headers plan
  - Outputs: HTTPS enforcement strategy, HSTS/header configuration notes.
  - Depends on: 2.1
- [x] 3.5 Add security-focused tests
  - Outputs: tests for rate-limit behavior and no-secret-in-log assertions.
  - Depends on: 3.1, 3.2, 3.3

## Phase 4 - UI and UX

- [x] 4.1 Build single-page input UI (`GET /`)
  - Outputs: domain input form + generate action.
  - Depends on: 2.2
- [x] 4.2 Render certificate and private key output panes
  - Outputs: separate read-only text areas for PEM results.
  - Depends on: 4.1
- [x] 4.3 Add copy-to-clipboard actions
  - Outputs: copy buttons and user feedback states.
  - Depends on: 4.2
- [x] 4.4 Add download as `.pem` actions
  - Outputs: downloadable cert/key files from generated content.
  - Depends on: 4.2
- [x] 4.5 Add validation and API error feedback in UI
  - Outputs: clear inline and global errors for 400/429/500 states.
  - Depends on: 2.4, 4.1
- [x] 4.6 Add responsive/mobile pass
  - Outputs: usable layout for small screens.
  - Depends on: 4.1, 4.2, 4.5

## Phase 5 - Observability

- [ ] 5.1 Add structured JSON request logging
  - Outputs: `{ timestamp, clientIP, domain, status, latency }` logging without secrets.
  - Depends on: 2.2, 3.3
- [ ] 5.2 Add application metrics
  - Outputs: counters for success/failure and latency metrics endpoint or exporter integration.
  - Depends on: 2.2
- [ ] 5.3 Add correlation/request IDs
  - Outputs: traceable request context through logs and errors.
  - Depends on: 5.1
- [ ] 5.4 Add observability tests
  - Outputs: tests for logging shape and key metrics increments.
  - Depends on: 5.1, 5.2

## Phase 6 - Containerization and Runtime

- [ ] 6.1 Create multi-stage Dockerfile (`python:3.12-slim` runtime)
  - Outputs: optimized image build with minimal runtime footprint.
  - Depends on: 0.3, 2.1
- [ ] 6.2 Run container as non-root user
  - Outputs: least-privilege runtime configuration.
  - Depends on: 6.1
- [ ] 6.3 Add healthcheck and runtime defaults
  - Outputs: health probe wiring and production-safe command startup.
  - Depends on: 2.3, 6.1
- [ ] 6.4 Add local container run profile
  - Outputs: developer command(s) for building/running/testing containerized app.
  - Depends on: 6.1, 6.3

## Phase 7 - CI/CD

- [ ] 7.1 Add CI workflow for lint, test, and build
  - Outputs: pipeline running on pushes/PRs with Python 3.12.
  - Depends on: 0.5, 6.1
- [ ] 7.2 Add container publish workflow
  - Outputs: image tagging and push to registry.
  - Depends on: 7.1
- [ ] 7.3 Add deployment workflow
  - Outputs: automated rollout steps for target environment.
  - Depends on: 7.2
- [ ] 7.4 Add CI artifacts and failure diagnostics
  - Outputs: test reports/log artifacts for troubleshooting.
  - Depends on: 7.1

## Phase 8 - Validation, Hardening, and Release

- [ ] 8.1 Run end-to-end flow validation
  - Outputs: tested journey from domain input to copy/download output.
  - Depends on: 4.6, 7.1
- [ ] 8.2 Run load/performance verification (target: 100+ RPS baseline)
  - Outputs: measured latency/throughput report and tuning notes.
  - Depends on: 6.4, 7.1
- [ ] 8.3 Run security review and dependency audit
  - Outputs: remediation list for vulnerabilities and misconfigurations.
  - Depends on: 3.5, 6.2
- [ ] 8.4 Finalize operational runbook
  - Outputs: startup, rollback, incident, and key-rotation procedures.
  - Depends on: 5.3, 7.3
- [ ] 8.5 Release readiness sign-off
  - Outputs: checklist approval for production launch.
  - Depends on: 8.1, 8.2, 8.3, 8.4

## Optional Future Tasks (Post-MVP)

- [ ] F.1 Add ACME/Let's Encrypt production issuance flow with challenge handling
  - Outputs: browser-trusted CA-signed certificates for public websites, replacing self-signed certificates that trigger browser warnings.
  - Depends on: 8.5
- [ ] F.2 Add CAPTCHA or bot-detection layer for public deployments
  - Depends on: 3.1
- [ ] F.3 Add audit dashboard for request trends and failures
  - Depends on: 5.2
- [ ] F.4 Add role-based access controls if app becomes private/internal
  - Depends on: 2.5
