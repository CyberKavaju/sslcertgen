---
description: "Authentication and RBAC rules for Flask. Apply when implementing login/logout, permissions, access guards, role checks, or any auth-related code."
name: "Auth and RBAC"
applyTo:
  - "app/**/*.py"
  - "tests/**/*.py"
---
# Authentication and RBAC Rules

## Permission Strings Over Role Names

- Authorization checks must key off granular permission strings (e.g. `import.run`, `report.schedule`, `user.manage`), not role labels alone.
- Permission constants are defined in `app/permissions.py`. Never hardcode permission strings inline.
- Core roles (`admin`, `manager`, `analyst`, `viewer`, `integration_bot`) group permissions — they do not replace per-action checks.

## Browser Auth: Session + CSRF

- First-party browser UI routes use session-based authentication via Flask-Security-Too.
- All state-changing browser requests (POST, PATCH, PUT, DELETE) require a valid CSRF token via Flask-WTF.
- Never use JWT or Bearer tokens as the primary auth mechanism for browser-rendered pages.

## Machine Auth: JWT or Personal Access Tokens

- API consumers, automation clients, and third-party integrations authenticate with Bearer JWT or hashed personal access tokens.
- JWT access tokens must have a short expiry; use refresh tokens for long-lived sessions.
- Revoked tokens must be checked against a blocklist (Redis or database) on every request.
- Never issue JWT tokens to browser UI flows.

## Per-Request Authorization

- Every protected route and service method must perform an explicit server-side authorization check.
- Check authorization after authentication — a valid session does not imply permission.
- Authorization failures must return `403 Forbidden`, never silently succeed or redirect without logging.

## Flask-Security-Too

- Use Flask-Security-Too as the default auth subsystem for user login, logout, password reset, profile management, and role/permission management.
- MFA is supported but optional for initial release; do not couple business logic to MFA state.
- SMS-based MFA belongs to the auth subsystem only — the general messaging/texting subsystem is separate.

## Definition Of Done

- Every protected route has a corresponding authorization test that asserts a `403` when the permission is absent.
- No role-name-only checks exist; all checks reference permission strings.
- Session and JWT paths are not mixed in the same flow.
