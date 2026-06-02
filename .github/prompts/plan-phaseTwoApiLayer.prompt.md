## Plan: Phase 2 API Layer Implementation

Implement Phase 2 by introducing a versioned API blueprint for certificate generation, preserving root health probes, standardizing error contracts, and adding integration coverage for happy/invalid/failure paths. The recommended approach is strict TDD by phase slice: write failing integration tests for endpoint contracts first, then implement minimal controller/schema/error wiring to pass.

**Steps**
Note: parenthetical references like `(2.1)` in Phases C-F refer to external todo IDs in Phase 2 (`2.1`-`2.5`) from `docs/todo.md`, not to Step B item numbers in this plan.
1. Phase A - Preconditions and contract lock
   1.1 Confirm route contract: use `/api/v1/generate` for generation endpoint while keeping `/healthz` at app root for probes.
   1.2 Keep response DTO shape aligned with existing schema objects (`certificate`, `key`) and define API error shape as `{ "error": "<code>", "message": "<human-readable>" }`; include optional `details` only for `400` validation errors as field-level validation messages, and never include exception text, stack traces, file paths, or request domain values.
   1.3 Enforce dependency direction (Controller -> Service -> Schema/Utils) and avoid business logic in controllers.
2. Phase B - TDD for routing skeleton and endpoint contracts
   2.1 Add/extend integration tests to assert blueprint registration and route availability for `POST /api/v1/generate` and `GET /healthz`. *blocks 3.x*
   2.2 Add failing integration tests for `POST /api/v1/generate` success path: valid domain returns `200` with non-empty PEM strings in `certificate` and `key` fields. *parallel with 2.3*
   2.3 Add failing integration tests for invalid input path: malformed/empty domain returns `400` with structured error payload and no sensitive details. *parallel with 2.2*
   2.4 Add failing integration tests for service failure path by monkeypatching certificate generation to raise runtime and unexpected exceptions (for example `ValueError` or `TimeoutError`); assert `500` with sanitized structured error payload. *depends on 2.1*
3. Phase C - Implement app factory and API routing (2.1)
   3.1 Create certificate controller blueprint under controllers with URL prefix `/api/v1` and register routes there.
   3.2 Wire blueprint registration inside extension initialization so app factory remains focused on composition, with a single allowed inline route definition for root health probing.
   3.3 Preserve existing root health probe behavior (`/healthz`) in app factory; do not move this route under `/api/v1` in Phase 2.
4. Phase D - Implement POST generate flow (2.2)
   4.1 Add request parsing/validation schema for incoming payload with required `domain` only in Phase 2; reject any `policy` key as unsupported input.
   4.2 In controller, require `application/json` and valid JSON body; if content type is incorrect or JSON is invalid, return `400` with `{ "error": "invalid_request", "message": "Request body must be valid JSON" }`; then validate request shape, call service `generate_certificate`, convert service result to response schema, and return JSON.
   4.3 Keep controller thin: no cert business rules or crypto logic in controller; all generation remains in service layer.
5. Phase E - Error model and status mapping (2.4)
   5.1 Add API error schema/object(s) for consistent JSON errors.
   5.2 Register centralized error handlers for validation/input errors (`400`), `RateLimitError` mapped to `429` with `{ "error": "rate_limited", "message": "Too many requests" }` (without wiring limiter triggers in Phase 2), `404` with `{ "error": "not_found", "message": "Resource not found" }`, `405` with `{ "error": "method_not_allowed", "message": "Method not allowed" }`, and unexpected server errors (`500`) with sanitized messages.
   5.3 Ensure `PolicyValidationError`, invalid/missing request fields, and invalid domain inputs map to `400`; domain validity is determined by the existing `validate_fqdn` rules (non-empty string and accepted FQDN format). Any uncaught service-layer exception maps to `500` as `{ "error": "generation_failed", "message": "Certificate generation failed" }`, with original exception details logged but not exposed.
6. Phase F - Finalize integration tests (2.5) and quality checks
   6.1 Stabilize integration fixtures (`app` and `client`) in shared test configuration for consistent endpoint tests.
   6.2 Complete/adjust integration assertions for valid domain, invalid domain, and internal failure to match finalized error contract.
   6.3 Run unit+integration gates and static checks; update todo checkboxes for completed 2.1-2.5 items only after tests pass.

**Relevant files**
- `/home/william/devs/sslcertgen/app/__init__.py` - keep app factory composition and root `/healthz` probe behavior.
- `/home/william/devs/sslcertgen/app/extensions.py` - register the API blueprint.
- `/home/william/devs/sslcertgen/app/controllers/certificate_controller.py` - new API blueprint and `POST /api/v1/generate` route handler.
- `/home/william/devs/sslcertgen/app/schemas/certificate_schema.py` - reuse existing `CertificateResponse`; add request schema and API error schema.
- `/home/william/devs/sslcertgen/app/services/certificate_service.py` - keep generation orchestration entrypoint used by controller; do not move HTTP concerns here.
- `/home/william/devs/sslcertgen/tests/conftest.py` - add reusable Flask app/client fixtures for integration tests.
- `/home/william/devs/sslcertgen/tests/integration/test_app_factory.py` - retain/adjust health and app wiring expectations.
- `/home/william/devs/sslcertgen/tests/integration/test_certificate_controller.py` - new integration coverage for Phase 2 endpoint scenarios.
- `/home/william/devs/sslcertgen/docs/todo.md` - mark 2.1-2.5 complete after verification.

**Verification**
1. Run targeted integration tests for app factory and certificate controller endpoints.
2. Run full unit+integration test selection using the project’s reliable invocation style (`/usr/bin/python3 -m pytest -m "unit or integration"`).
3. Validate structured error responses manually with test client for representative 400 and 500 paths; confirm no stack traces/internal details leak.
4. Run lint/type checks (`ruff check`, `ruff format --check`, `mypy app`) before considering Phase 2 complete.

**Decisions**
- Endpoint namespace: include `/api/v1` for generation endpoint.
- Health probe location: keep `/healthz` at root.
- Included scope: Phase 2.1-2.5 only (routing, generate endpoint, health probe validation, error mapping, integration tests).
- Excluded scope: Phase 3 rate-limiter behavior enforcement beyond 429 contract scaffolding, UI work, observability/metrics, container/CI changes.

**Further Considerations**
1. Error code taxonomy recommendation: use stable machine codes (`invalid_request`, `invalid_domain`, `generation_failed`, `rate_limited`) from day one to avoid client-breaking renames.
2. If policy input is exposed in Phase 2 request body, limit accepted fields to current schema and reject unknown keys to keep boundary strict.
3. Keep PEM content assertions in tests structural (header/footer presence) rather than full cryptographic deep inspection to avoid brittle integration tests.
