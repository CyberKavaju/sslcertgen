## Plan: Phase 3 Security and Abuse Protection

Implement Phase 3 end-to-end by adding boundary protections first (rate limiting + payload/domain limits), then leakage guardrails, then HTTPS/proxy/header strategy, and finally security-focused tests that prove regressions are blocked. This follows existing Flask MVC layering and current error contract patterns while keeping private key handling strictly in-memory.

**Steps**
- A1. Phase A: Baseline decisions and constants.
- A2. Confirm and lock Phase 3 defaults in config surface: `RATE_LIMIT_PER_IP` default = `10/minute`, `MAX_CONTENT_LENGTH` default = `8192` bytes, `MAX_DOMAIN_LENGTH` default = `253`, and explicit HTTPS/proxy/header toggles. Use app config methods so tests can monkeypatch env values consistently. Depends on A1.
- A3. Define explicit error contract mapping for new protections: `429` for throttling, `413` for oversized payload, `400` for malformed JSON/domain validation. Reuse current structured error shape `{error, message, details?}`. Depends on A2.

- B1. Phase B: Implement 3.1 per-IP rate limiting.
- B2. Add limiter extension wiring in app extension bootstrap with `ProxyFix` configured as `x_for=TRUST_PROXY_HOPS` (default `1`) and derive the rate-limit key from the leftmost trusted forwarded IP. Depends on A2.
- B3. Attach endpoint-specific limit to `POST /api/v1/generate` route (controller boundary), preserving controller-only HTTP concerns and avoiding service-layer coupling. Depends on B2.
- B4. Add limiter-to-API error translation so rate-limit violations return standardized JSON `429` (`rate_limited`, `Too many requests`) through current exception/error-handler pattern. Depends on B3.

- C1. Phase C: Implement 3.2 request and input boundaries.
- C2. Enforce request body size via app-level content length guard (`MAX_CONTENT_LENGTH`) to return `413` before expensive parsing. If `Content-Length` is missing or chunked transfer encoding is used, read the body up to `MAX_CONTENT_LENGTH + 1` bytes and return `413` if exceeded. Depends on A2.
- C3. Tighten schema payload validation in `GenerateCertificateRequest`: enforce domain max length (`<=253`), reject blank/whitespace-only domain, keep explicit `policy` field rejection, and reject unknown fields (allow only `domain`) to enforce strict boundaries in Phase 3. Depends on C2.
- C4. Add explicit handling for malformed JSON/body edge cases in controller path (invalid JSON syntax, missing JSON body) to maintain deterministic `400` responses and avoid internal errors. Depends on C3.

- D1. Phase D: Implement 3.3 sensitive-data leakage guardrails.
- D2. Audit and harden error/detail shaping so user-supplied payload fragments and secrets are not echoed unexpectedly; keep private key material out of exceptions, logs, and error details. Depends on A3.
- D3. Add a small response/log redaction utility at boundary level (schema or app-level helper) for any future sensitive fields and use it in error serialization path. Depends on D2.
- D4. Verify no persistence path exists for private keys (files/DB/repositories) and keep current in-memory-only service flow unchanged. This is a guardrail check, not a feature expansion. Depends on D3.

- E1. Phase E: Implement 3.4 TLS/proxy trust and security headers plan.
- E2. Document deployment trust model for reverse proxy setup: client -> TLS terminator -> Flask app, including trusted hop count and forwarded-header assumptions. Depends on A2.
- E3. Add configurable HTTPS enforcement strategy (app/proxy responsibilities) and security headers policy notes (`HSTS`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP baseline: `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`). Depends on E2.
- E4. Record operational verification checklist for headers and proxy behavior (curl/functional checks) in docs so Phase 6 deployment work can apply it directly. Depends on E3.

- F1. Phase F: Implement 3.5 security-focused tests (TDD).
- F2. Add/extend integration tests for rate limiting: threshold exceeded returns `429` with expected JSON contract; non-exceeded requests remain `200`; per-IP behavior tested through request environ/header setup. Configure limiter with in-memory storage for tests, reset limiter state between tests in a fixture, and allow per-test override of `RATE_LIMIT_PER_IP`. Depends on B4.
- F3. Add/extend integration tests for request limits: oversized payload returns `413`, malformed JSON returns `400`, invalid domain length returns `400` with stable error payload. Depends on C4.
- F4. Add logging-focused tests using `caplog` to assert private key markers (`BEGIN PRIVATE KEY`/`END PRIVATE KEY`) are never emitted in log records for success and failure paths. Depends on D4.
- F5. Add/extend unit tests for config helpers and schema validators covering new boundary constants and edge-case validation messages. Depends on A2 and C3.

- G1. Phase G: Finish and verify.
- G2. Run targeted tests first (new/changed files), then full unit+integration suite using `/usr/bin/python3 -m pytest -m "unit or integration"`. Depends on F2-F5.
- G3. If error contracts changed, update the todo checklist statuses and any API/security documentation references accordingly. Depends on G2.

**Relevant files**
- `/home/william/devs/sslcertgen/app/extensions.py` — initialize Flask-Limiter and connect limiter error handling to app boundaries.
- `/home/william/devs/sslcertgen/app/controllers/certificate_controller.py` — apply route rate limit and keep malformed/invalid request handling centralized at controller layer.
- `/home/william/devs/sslcertgen/app/config.py` — add security boundary config methods (rate/payload/domain/proxy/header toggles).
- `/home/william/devs/sslcertgen/app/__init__.py` — register error handlers and optional request/response hooks for payload/header policies.
- `/home/william/devs/sslcertgen/app/schemas/certificate_schema.py` — tighten request schema boundaries and sanitize error details.
- `/home/william/devs/sslcertgen/tests/integration/test_certificate_controller.py` — add 429/413/malformed/long-domain integration coverage and no-secret error behavior assertions.
- `/home/william/devs/sslcertgen/tests/integration/test_app_factory.py` — validate app wiring for boundary/security middleware behavior where appropriate.
- `/home/william/devs/sslcertgen/tests/unit/schemas/test_certificate_schema.py` — add request-boundary unit tests for domain limits and sanitization behavior.
- `/home/william/devs/sslcertgen/tests/unit/test_config.py` — add env-driven config tests for new security limits/toggles.
- `/home/william/devs/sslcertgen/docs/prd.md` — align/append TLS-proxy/security-header planning notes for Phase 3.4 output.
- `/home/william/devs/sslcertgen/docs/todo.md` — mark completed Phase 3 tasks after verification.

**Verification**
- V1. Run targeted security integration tests: `/usr/bin/python3 -m pytest tests/integration/test_certificate_controller.py -q`.
- V2. Run targeted app wiring tests: `/usr/bin/python3 -m pytest tests/integration/test_app_factory.py -q`.
- V3. Run targeted unit tests: `/usr/bin/python3 -m pytest tests/unit/schemas/test_certificate_schema.py tests/unit/test_config.py -q`.
- V4. Run full quality subset: `/usr/bin/python3 -m pytest -m "unit or integration"`.
- V5. Confirm expected contracts manually from test assertions.
- V6. Confirm `429` JSON for throttling includes `error=rate_limited`.
- V7. Confirm `413` JSON for oversized payload is structured and non-leaky.
- V8. Confirm `400` JSON for malformed/invalid input remains structured and non-leaky.
- V9. Confirm log capture contains no private key PEM markers.
- V10. For Phase 3.4 docs output, manually verify headers/proxy checklist can be executed with curl in deployment phase.

**Decisions**
- Included scope: full Phase 3 tasks 3.1 through 3.5 (implementation plus tests), per user confirmation.
- Reuse existing files and patterns first (controller integration tests + schema/config unit tests) before introducing new test modules.
- Keep MVC boundaries strict: controller handles HTTP concerns, service remains cert-generation business logic only.
- Preserve existing API error envelope and avoid exposing internal details.
- Treat TLS/proxy/header item as a concrete documentation and configuration strategy deliverable (not full production ingress implementation yet).

**Further Considerations**
- FC1. Rate-limit storage backend for future horizontal scaling: in-memory backend now (simple) vs Redis backend later (production-consistent). Recommendation: implement in-memory now, document Redis as Phase 6/8 hardening.
- FC2. On limiter backend errors (for future Redis-backed mode), fail-open (allow request) and log a warning; do not return `500` to clients.
- FC3. Unknown request fields policy is decided for Phase 3: reject extras and allow only `domain`.
- FC4. Header responsibility split: set headers in Flask and enforce/override at reverse proxy for defense in depth.