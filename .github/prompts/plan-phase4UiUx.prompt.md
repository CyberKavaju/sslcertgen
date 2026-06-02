## Plan: Phase 4 UI/UX Single-Page Experience

Deliver Phase 4.1 through 4.6 in one batch by adding a server-rendered Flask page at root, wiring it to the existing POST generation API, and implementing client-side interactions for result rendering, copy, download, error feedback, and responsive behavior. This approach preserves existing API contracts, follows MVC boundaries, and keeps verification centered on integration tests as requested.

**Steps**
Phase A - TDD setup and failing tests
A.1 Add or update integration tests first for root page behavior and UI contract presence in HTML, including expected form fields, action controls, output panes, and error container markers. Mark tests with integration marker and use existing client fixture patterns. Depends on existing patterns in tests/integration/test_app_factory.py and tests/integration/test_certificate_controller.py.
A.2 Add integration tests for CSP/header compatibility expectations required by the new UI delivery path, ensuring security headers remain present and CSP includes only the minimal allowances needed for Tailwind CDN and page script execution. Depends on A.1.

Phase B - Backend routing and app wiring
B.1 Introduce a dedicated UI controller at app/controllers/ui_controller.py with one blueprint and a GET root route that returns the certificate page template. Keep controller limited to request-response concerns and do not add business logic. Depends on A.1.
B.2 Register the UI blueprint via app/extensions.py following current lazy-import blueprint registration style to avoid circular imports and maintain layer direction. Depends on B.1.
B.3 Update app factory creation in app/__init__.py to enable template and static directories and preserve existing middleware/error behavior. Adjust error handling path so unknown UI routes can still be rendered safely later without changing current API error contracts now. Depends on B.2.
B.4 Update CSP source in app/config.py with a minimal default policy that still enforces strict baseline but allows required CDN/script/style/font sources for this specific UI architecture. Depends on A.2.

Phase C - Template architecture and design-system foundation
C.1 Create base layout at app/views/layouts/base.html with required head dependencies, canonical Tailwind token config, Inter and Material Symbols includes, and the glass classes defined in .github/instructions/ui-design-system.instructions.md: glass-card, glass-panel, glass-card-elevated, and glass-panel-elevated. Depends on B.3 and B.4.
C.2 Create reusable macros under app/views/components/ for buttons and panel/card wrappers used by the page to prevent duplicated markup from first reuse. Depends on C.1.
C.3 Create feature page template at app/views/certificate/index.html extending the base layout, containing domain input form, generate action, read-only certificate and private-key panes, copy actions, download actions, inline validation slot, global API-error slot, and semantic state hooks for JS. Depends on C.2.

Phase D - Client-side behavior and UX completion
D.1 Add app/static/js/certificate_page.js (or equivalent feature-scoped file) to implement:
- domain pre-submit validation using regex ^(?=.{1,253}$)([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$, with empty input rejected and an inline message in the validation slot;
- submit flow with a single in-flight request (disable generate button, show loading state, and ignore additional submits while pending);
- POST to /api/v1/generate and success rendering into separate certificate and key panes;
- copy-to-clipboard with navigator.clipboard when available, fallback to hidden textarea plus document.execCommand("copy"), and an error state with manual-copy guidance on failure;
- .pem download actions using sanitized filenames <domain>.cert.pem and <domain>.key.pem, where non-alphanumeric characters are replaced with _;
- explicit response mapping: 400 -> inline validation slot with server message, 429 -> global API-error slot with rate-limit message, 500 -> global API-error slot with generic retry message;
- fetch rejection or non-mapped statuses -> global API-error slot with "Network error, please retry" while keeping current form state intact.
Depends on C.3.
D.2 Add app/static/css/certificate_page.css only for rules not cleanly expressible via tokenized utilities, while preserving the Frozen Light rules from .github/instructions/ui-design-system.instructions.md (including no opaque solid card backgrounds, no shadow-md/shadow-lg, no inline raw hex colors in HTML/Jinja, and no duplicate component markup). Keep responsive breakpoints mobile-first. Depends on C.3.
D.3 Ensure responsive/mobile pass for narrow widths: stacked layout, readable controls, no horizontal overflow, and accessible touch targets for copy/download actions. Depends on D.1 and D.2.

Phase E - Verification and task closure
E.1 Run integration tests and targeted files first, then full unit+integration suite via project command path. Confirm no regressions in existing API and security-header behavior. Depends on B.1 through D.3.
E.2 Manually verify browser flow for a valid domain and representative invalid/error cases, including copy/download behavior and mobile viewport checks. Depends on E.1.
E.3 Update docs/todo.md by marking Phase 4.1 through 4.6 complete only after verification passes. Depends on E.2.

**Parallelism and Dependencies**
1. C.1 can begin once both B.3 and B.4 are complete.
2. C.2 and C.3 are sequential due to template inheritance and macro reuse.
3. D.1 and D.2 can run in parallel after C.3, then converge at D.3.
4. Verification (E.1 to E.3) is strictly sequential and blocks final completion.

**Relevant files**
- /home/william/devs/sslcertgen/app/__init__.py - Flask app factory create_app, template/static configuration, security header application, and global error handlers.
- /home/william/devs/sslcertgen/app/config.py - BaseConfig.content_security_policy default string and env override contract.
- /home/william/devs/sslcertgen/app/extensions.py - init_extensions blueprint registration pattern with lazy imports.
- /home/william/devs/sslcertgen/app/controllers/certificate_controller.py - Existing API controller pattern to mirror for new UI controller boundaries.
- /home/william/devs/sslcertgen/app/controllers/ui_controller.py - New root UI controller and blueprint.
- /home/william/devs/sslcertgen/app/views/layouts/base.html - Shared layout shell with required design-system setup.
- /home/william/devs/sslcertgen/app/views/components/buttons.html - Reusable button macros for generate/copy/download controls.
- /home/william/devs/sslcertgen/app/views/components/cards.html - Reusable glass card/panel macros for result panes and error container.
- /home/william/devs/sslcertgen/app/views/certificate/index.html - Single-page certificate UX template.
- /home/william/devs/sslcertgen/app/static/js/certificate_page.js - Frontend behavior for generate/copy/download/error mapping.
- /home/william/devs/sslcertgen/app/static/css/certificate_page.css - Feature-specific responsive refinements if needed.
- /home/william/devs/sslcertgen/tests/integration/test_app_factory.py - Header/CSP behavior assertions to extend.
- /home/william/devs/sslcertgen/tests/integration/test_ui_controller.py - New integration tests for GET root UI behavior.
- /home/william/devs/sslcertgen/tests/integration/test_certificate_controller.py - Existing API error contract expectations used by UI mapping.
- /home/william/devs/sslcertgen/docs/todo.md - Phase checklist updates after successful verification.

**Verification**
1. Run focused integration tests for new UI route and app factory headers using /usr/bin/python3 -m pytest with integration marker targeting modified tests.
2. Run complete project test command for unit plus integration coverage via just test. If just test is unavailable, run /usr/bin/python3 -m pytest -m "unit or integration" --cov=app.
3. Manually validate in browser: valid domain generation path, invalid domain path, synthetic rate-limit path, and simulated server-error path.
4. Manual UI checks: copy buttons show feedback and clipboard receives expected PEM, download buttons produce separate .pem files with expected names and content.
5. Manual responsive checks at common mobile widths to confirm layout stacking, readability, and control usability.

**Decisions**
- Included scope: Full Phase 4.1 to 4.6 in one batch.
- Testing depth decision: Integration tests required; E2E Playwright intentionally excluded for this phase.
- CSP decision: Minimal and temporary policy relaxation to support Tailwind CDN and required page assets for Phase 4, with a planned follow-up to tighten policy when assets move local.
- Architecture decision: New UI controller blueprint for GET root route; API controller remains JSON-only.
- Excluded scope: New backend API fields, auth changes, persistence, or observability work from later phases.

**Further Considerations**
1. Error rendering strategy recommendation: Keep server errors JSON for API endpoints and handle user-facing messaging entirely in page JS for this phase, then consider optional HTML error template work in a later hardening task.
2. Asset strategy recommendation: Start with CDN Tailwind for this phase and explicitly schedule a follow-up task to migrate to bundled local assets and tighten CSP in the same change.
3. Accessibility recommendation: Add lightweight keyboard and aria checks during manual verification so copy/download controls are operable without pointer input.