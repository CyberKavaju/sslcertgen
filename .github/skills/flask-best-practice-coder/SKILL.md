---
name: flask-best-practice-coder
description: 'Write Flask code using official Pallets documentation and proven patterns. Use when implementing features, fixing bugs, structuring app factories and blueprints, configuring environments, handling errors, adding logging, and testing Flask apps with docs-backed decisions.'
argument-hint: 'Describe the Flask task, current code, architecture constraints, and whether this is API-only, server-rendered, or mixed.'
user-invocable: true
disable-model-invocation: false
---

# Flask Best Practice Coder

Use this skill to implement Flask code with a docs-first workflow grounded in the official Flask documentation.

## Outcome
- Produce maintainable Flask code that follows official patterns.
- Make decisions traceable to Flask docs, not guesswork.
- Include testing, configuration, and operational safeguards by default.

## When to Use
- Building new Flask modules, routes, services, or CLI commands.
- Refactoring Flask apps into app factory and blueprint structure.
- Improving configuration handling for dev, test, and production.
- Standardizing error handling and logging behavior.
- Adding or fixing Flask tests and request lifecycle behavior.

## Inputs to Gather First
- Flask version and Python version.
- Current architecture: single app, app factory, or multi-blueprint.
- Type of endpoint: HTML/template, JSON API, or mixed.
- Persistence layer and extensions in use.
- Constraints: performance, security, deployment target, and test expectations.

## Core Workflow
1. Restate the coding task and success criteria in one short paragraph.
2. Fetch relevant Flask docs before coding. Use [Flask Official Docs Map](./references/flask-official-doc-map.md) to select pages.
3. Choose structure first:
   - Use application factory (`create_app`) for non-trivial apps.
   - Register blueprints for modular features.
   - Initialize extensions with `init_app` instead of binding at import time.
4. Load configuration early in app setup so extensions can read it during initialization.
5. Implement request handlers with explicit input validation and explicit HTTP status codes.
6. Add targeted error handlers; avoid overly broad exception handlers unless carefully passing through `HTTPException`.
7. Configure logging as early as possible; avoid accidental default handler behavior from late setup.
8. Add or update tests for request behavior, session behavior, and CLI commands as applicable.
9. Confirm production-safe behavior:
   - No debug mode in production.
   - Development server not used for production runtime.
   - Secret and environment handling follow docs guidance.
10. Summarize changes with doc references and list residual risks.

## Decision Points and Branching

### A) App Structure
- If app is growing beyond a few routes: switch to factory + blueprints.
- If extension objects are currently app-bound at import time: refactor to extension objects created once and bound in `create_app` via `init_app`.

### B) Configuration
- If config differs by environment: use a default config plus environment-specific override.
- If secrets are present in code: move to environment-based loading and instance/deployment-specific files.
- If testing is hard due to global config assumptions: pass test config into the factory.

### C) Error Handling
- If API endpoints return HTML error pages: add JSON-focused handlers for relevant exceptions.
- If a generic `Exception` handler exists: ensure `HTTPException` instances pass through unless there is an intentional transformation.
- If blueprint-level 404/405 handling is expected for routing misses: move those strategies to app-level handling by URL prefix.

### D) Logging
- If logs are configured after first logger access: remove or replace default handler intentionally.
- If production observability is weak: add structured context and error notification strategy.

### E) Testing
- If app uses factory pattern: create fixtures that instantiate app with test config.
- If commands are untested: use Flask CLI runner tests.
- If code depends on context globals (`request`, `session`, `current_app`): use explicit app or request context tests.

## Quality Gates
- Official Flask docs were fetched and used for each non-trivial decision.
- App setup remains deterministic and completed before serving requests.
- Config, extension init, and blueprint registration follow factory-compatible patterns.
- Error responses are explicit and consistent with endpoint type (HTML vs JSON).
- Logging is configured early and intentionally.
- Tests cover happy path plus at least one failure path per changed route or command.

## Completion Checklist
- Code compiles and runs in development mode via Flask CLI.
- Relevant tests pass.
- No production anti-patterns introduced (debug in prod, dev server as prod, secrets in source).
- Final output includes exact docs consulted and why each one mattered.

## Common Pitfalls
- Modifying app setup during request handling.
- Reading config at import time before factory setup.
- Binding extensions to app instances too early.
- Returning incorrect status codes from error handlers.
- Relying on broad exception handlers that mask HTTP semantics.

## Recommended Output Format
1. Task summary and architecture choice.
2. Docs consulted and extracted rules.
3. Implementation changes.
4. Tests added or updated.
5. Risks and follow-up improvements.

## References
- [Flask Official Docs Map](./references/flask-official-doc-map.md)
- https://flask.palletsprojects.com/en/stable/
