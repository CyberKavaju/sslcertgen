## Plan: Phase 0 Foundation Execution

Finalize and implement Phase 0 by locking decisions (Flask, self-signed MVP, Docker behind reverse proxy), then creating a minimal scaffold including: app factory pattern, config-by-environment, structured logging setup, and a /healthz endpoint stub that aligns with repo instructions (Flask MVC structure, security constraints, and CI quality gates). The approach is to make CI pass early with pinned dependencies, environment contracts, and a single local command that mirrors CI checks.

**Steps**
1. Phase 0.1 - Confirm scope defaults and record them in project docs. Include explicit decisions: Flask framework, self-signed certificates first, deployment target as single Docker container behind reverse proxy. This unblocks all remaining foundation tasks.
2. Phase 0.2 - Initialize repository layout per folder-structure instructions. Create app and tests baseline directories/files, plus deployment and docs placeholders required by upcoming phases. Keep __init__ files registration-only and avoid business logic. If a target file or directory already exists, do not overwrite it; diff against planned content, surface differences, and request confirmation before modifying.
3. Phase 0.3 - Establish Python environment and dependency manifests with pinned versions. Add runtime and dev/test manifests designed to satisfy current CI workflow checks (ruff, mypy, pytest-cov). Select versions compatible with Python 3.12 and Flask 3. If pip resolution fails, stop and report the conflicting packages; do not relax pins without explicit approval.
4. Phase 0.4 - Define environment configuration contract. Add a documented env template and config module contract for app mode, log level, rate limiting, and TLS/proxy trust behavior. Include safe defaults and explicit required vs optional variables.
5. Phase 0.5 - Add quality gates and local automation. Provide one entrypoint command that runs format/lint, typing, and tests in CI order. Ensure commands and flags match CI to reduce local-vs-CI drift. If a tool flag in ci.yml is ambiguous or undocumented, prefer the strictest reasonable default and log the assumption in docs/todo.md.
6. Update Phase 0 checklist state in docs/todo.md once each task is complete (0.1 through 0.5) and include short notes or links to artifacts.

**Execution ordering and parallelism**
1. Steps 1 and 2 are sequential; step 2 depends on step 1 decisions.
2. Steps 3 and 4 can partially overlap after step 2; step 4 finalizes after dependency/tool choices in step 3.
3. Step 5 starts only after both steps 3 and 4 are complete.
4. Step 6 is final and depends on completion evidence from steps 1-5.

Precedence: Decisions are binding. Further Considerations are advisory and may be overridden with justification.

**Relevant files**
- /home/william/devs/sslcertgen/docs/prd.md - source of defaults and non-functional constraints.
- /home/william/devs/sslcertgen/docs/todo.md - task checklist to update with completion status.
- /home/william/devs/sslcertgen/.github/workflows/ci.yml - required quality checks to mirror locally.
- /home/william/devs/sslcertgen/.github/instructions/folder-structure.instructions.md - required file placement and naming.
- /home/william/devs/sslcertgen/.github/instructions/tdd.instructions.md - required testing workflow for Python changes.
- /home/william/devs/sslcertgen/.github/instructions/security.instructions.md - required security baseline for config/input/secrets handling.

**Planned artifacts to create in this phase**
1. Project scaffold: app/, app/controllers/, app/services/, app/repositories/, app/models/, tests/unit/, tests/integration/, tests/e2e/, tests/factories/, tests/fixtures/, deployment/, docs/.
2. Dependency manifests: runtime and dev/test pinned requirement files.
3. Environment contract: env template and app config module.
4. Local automation entrypoint: use a justfile by default; only fall back to a Makefile if the CI runner image does not include just.
5. Documentation updates capturing final Phase 0 defaults and checklist completion.

**Phase 0.6 - Verification**
1. Confirm Python 3.12 is available locally before verification. If Python 3.12 is unavailable, halt verification and report the missing prerequisite rather than falling back to another version.
2. Run local dependency install for runtime and dev manifests on Python 3.12.
3. Run lint and formatting checks with the same tools used in CI.
4. Run static typing checks against the application package.
5. Run test suite with coverage threshold read from .github/workflows/ci.yml --cov-fail-under flag and mirror it exactly.
6. Validate env contract by launching app in development and testing config modes.
7. Confirm CI workflow executes without missing-file errors (especially requirements-dev and test config assumptions).

**Decisions**
- Framework: Flask.
- Certificate mode for MVP: self-signed only.
- Deployment target: single Docker container behind reverse proxy.
- In Phase 0, only record the self-signed decision in docs/prd.md; do not create cert-generation modules.
- Scope included: only tasks 0.1 to 0.5 and their enabling docs/config/tooling.
- Scope excluded: domain validation implementation, cert generation logic, API endpoint implementation, and container hardening beyond baseline planning.

**Further Considerations**
1. Local automation tool choice: keep justfile as default unless team requires Makefile parity.
2. Version pin strategy: exact pins for CI reproducibility, then periodic controlled upgrades.
3. Early baseline tests: add one smoke test for app factory/config loading to satisfy TDD expectations from the start.
