## Plan: Phase 1 Core Domain Logic

Implement Phase 1 as a strict TDD sequence that creates a reusable domain validator, a certificate generation service with policy controls, and secure DTO output shaping, then closes with comprehensive unit coverage and quality-gate validation. This plan follows repo rules for layer boundaries, folder structure, and security (especially no key leakage).

**Steps**
1. Phase A - Baseline and test scaffolding
	1.1 Confirm imports, markers, and existing app/test conventions to mirror from app factory/config tests before adding new modules.
	1.2 Create test module shells that mirror app structure under tests/unit for utils, services, and schemas; keep naming aligned with feature-based conventions. This can run in parallel with Phase B step 2.1.

2. Phase B - Task 1.1 strict FQDN validator (blocks all later domain work)
	2.1 Write failing unit tests first for normalization + validation behavior.
	2.2 Accept ASCII FQDN labels and punycode labels (xn--) only.
	2.3 For labels beginning with xn--, validate that they decode via IDNA 2008 (idna.decode). Reject if decoding fails. Return the original ASCII form as canonical output.
	2.4 Reject Unicode input, wildcard input, single-label hosts, illegal characters, over-length domains, and invalid label boundaries.
	2.5 Accept trailing dot but normalize it away before returning canonical domain.
	2.6 Implement app/utils/fqdn_validator.py with small pure functions:
		- normalize_fqdn(domain: str) -> str for trimming/canonicalization.
		- validate_fqdn(domain: str) -> str returning canonical domain or raising domain-specific validation exception.
		- Define class InvalidFQDNError(ValueError). Error message format: "Invalid FQDN: <reason>". Do not echo raw user input in messages.
	2.7 Refactor only after tests are green; keep module free from Flask/service imports.

3. Phase C - Task 1.2 cert/key generation service (depends on 1.1)
	3.1 Write failing service tests first for happy path and failure path.
	3.2 Valid domain returns in-memory PEM cert + PEM key.
	3.3 Invalid domain raises a safe service/domain error.
	3.4 Generated cert includes CN and SAN for canonical domain.
	3.5 Implement app/services/certificate_service.py service entrypoint that:
		- Calls validator first.
		- Generates keypair and self-signed X.509 certificate via cryptography in memory.
		- Uses cryptography>=41 APIs. Serialize private key as PKCS8 PEM with NoEncryption(); serialize certificate as PEM. Document serialization format in the service docstring.
		- Wraps key/cert generation in try/except; on cryptography errors, raises CertificateGenerationError with a sanitized message that excludes stack traces and internal state.
		- Returns raw PEM strings only, without logging key material.
	3.6 Define internal exceptions in app/services or shared app/schemas/app/utils as needed for clear error semantics.

4. Phase D - Task 1.3 policy options (depends on 1.2)
	4.1 Write failing tests first for policy combinations and validation.
	4.2 Algorithms: RSA and EC.
	4.3 RSA key sizes: 2048/3072/4096.
	4.4 EC curves: P-256/P-384.
	4.5 Validity days bounded by min=1 and max=825.
	4.6 Subject fields configurable (CN required; O/OU/C optional) with validation rules: CN<=64, O<=64, OU<=64, and C must be exactly 2 alphabetic characters if provided. Raise PolicyValidationError on violation.
	4.7 SAN rules configurable with default domain-only SAN; enforce DNS SAN shape. Phase 1 SAN supports the primary canonical domain only; multi-entry SAN support is deferred.
	4.8 Add app/schemas/certificate_schema.py policy models using @dataclass(frozen=True) classes with explicit validation helpers; do not introduce pydantic in Phase 1.
	4.9 Extend certificate service signature to accept policy object and apply options safely.
	4.10 Reject policy objects where algorithm-specific fields are inconsistent (for example, curve provided for RSA or key_size provided for EC) with PolicyValidationError before any key generation.
	4.11 Keep default policy values centralized (app/config.py or schema defaults) and covered by tests.

5. Phase E - Task 1.4 secure output shaping (depends on 1.2, uses 1.3 model types)
	5.1 Write failing tests first for DTO contract.
	5.2 Canonical API-facing fields: certificate and key.
	5.3 Provide internal aliases certificate_pem/private_key_pem only on the internal service-layer return type; external DTO always uses certificate and key.
	5.4 No debug internals, key metadata, stack traces, or sensitive context in DTO serialization.
	5.5 Add response DTOs in app/schemas/certificate_schema.py and service mapping helpers in app/services/certificate_service.py.
	5.6 Override __repr__ and __str__ on any DTO containing key material to redact the key field. Never include private key bytes in __repr__ or __str__.

6. Phase F - Task 1.5 unit test completion + quality gate
	6.1 Expand/finish unit suites for edge-case matrix across validator + certificate generation + policy + DTO shaping.
	6.2 Add focused negative tests for malformed SAN entries, unsupported algorithm/key-size combinations, invalid validity ranges, and PEM parseability.
	6.3 Run local quality gates in dependency order:
		- pytest -m "unit" tests for new modules.
		- ruff check for lint.
		- mypy app for type checks.
		- Existing repo test coverage command to confirm no regressions.
	6.4 Keep tests deterministic and fast (no network/disk). For cryptographic operations, assert structural properties (CN, SAN, key type, validity range) rather than exact bytes. Do not seed or mock RNG.

**Parallelism and Dependencies**
1. Phase A step 1.2 test file scaffolding can run in parallel with baseline review.
2. Task order is serial for implementation: 1.1 -> 1.2 -> 1.3 -> 1.4 -> 1.5.
3. Early drafting of 1.4 DTO tests can start once 1.2 service output contract is known, but final DTO implementation follows 1.3 model decisions.

**Relevant files**
- /home/william/devs/sslcertgen/app/config.py - existing config patterns and defaults; extend for domain/cert defaults only if needed.
- /home/william/devs/sslcertgen/app/__init__.py - reference app style only; no Phase 1 route changes required.
- /home/william/devs/sslcertgen/app/services/certificate_service.py - new core certificate orchestration service.
- /home/william/devs/sslcertgen/app/utils/fqdn_validator.py - new strict FQDN normalization/validation helper.
- /home/william/devs/sslcertgen/app/schemas/certificate_schema.py - new policy + output DTO definitions.
- /home/william/devs/sslcertgen/tests/unit/test_config.py - style reference for pytest markers/structure.
- /home/william/devs/sslcertgen/tests/unit/utils/test_fqdn_validator.py - new validator unit tests.
- /home/william/devs/sslcertgen/tests/unit/services/test_certificate_service.py - new service/policy unit tests.
- /home/william/devs/sslcertgen/tests/unit/schemas/test_certificate_schema.py - new DTO contract tests.
- /home/william/devs/sslcertgen/tests/conftest.py - shared fixtures if test duplication appears.

**Verification**
1. Execute pytest unit suites for validator/service/schema and verify all tests are marked unit.
2. Parse generated PEM in tests using cryptography loaders to verify certificate/key format and certificate SAN/CN correctness.
3. Confirm invalid-domain and invalid-policy tests fail with sanitized error messages only.
4. Run lint/type checks and existing check-all command from justfile.
5. Manually inspect logs/assertions to ensure private key text is never logged or exposed in failure payload objects.

**Decisions**
- Enforce ASCII-only FQDN input with punycode labels allowed; reject Unicode input.
- Normalize trailing dot away before certificate generation.
- Reject wildcard domains and single-label hosts.
- For labels beginning with xn--, validate decode via IDNA 2008 and keep ASCII punycode form as canonical output.
- Policy scope includes RSA and EC, configurable key sizes/curves, validity bounds (1..825 days), subject options, and SAN rules.
- Phase 1 SAN supports primary canonical domain only; multi-entry SAN support is deferred.
- API-facing output field names remain certificate and key; internal alias handling is allowed but not exposed externally.

**Scope Boundaries**
- Included: domain validation, in-memory certificate generation, policy handling, secure DTO shaping, unit tests.
- Excluded: endpoint/controller wiring, persistence, rate limiting, UI integration, async/background processing (handled in later phases).

**Further Considerations**
1. Decide whether subject country code should enforce ISO 3166-1 alpha-2 format when provided.