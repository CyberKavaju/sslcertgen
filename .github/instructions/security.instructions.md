---
description: "Python and PostgreSQL security rules. Apply when writing or reviewing any Python, SQL, HTML, or template file — especially routes, models, forms, and anything handling user input or credentials."
name: "Security Rules"
applyTo:
  - "**/*.py"
  - "**/*.sql"
  - "**/*.html"
  - "**/*.jinja"
  - "**/*.j2"
---
# Security Rules

## Input Validation

- Treat all external input — request bodies, query strings, headers, uploaded files, webhook payloads — as untrusted.
- Validate and sanitize at the system boundary before any processing or persistence.
- Prefer allowlists for accepted values instead of broad deny lists.

## Database Access

- Use parameterized queries or ORM query APIs exclusively. Never build SQL strings with string interpolation or concatenation.
- Do not expose raw database errors or query details in API responses or logs.

## Authorization

- Enforce authorization checks server-side on every protected action — never rely on hidden UI elements or front-end route guards alone.
- Check permissions, not just authentication, for every state-changing or sensitive read operation.

## Secrets and Credentials

- Do not hardcode secrets, tokens, API keys, or database credentials in source code or committed config files.
- Load secrets from environment variables or a secrets manager at runtime.

## Password Storage

- Use Argon2id (preferred) or bcrypt for password hashing. Never store passwords in plaintext or use reversible encryption.
- Never log, return, or serialize password hashes in API responses.

## CSRF Protection

- Apply CSRF protection to all state-changing browser form requests (POST, PATCH, PUT, DELETE).
- Use Flask-WTF CSRF tokens for server-rendered forms.

## Data Exposure

- Never include stack traces, internal error messages, or sensitive field values in API error responses.
- Avoid logging PII, passwords, tokens, or financial values.

## Dependencies

- Keep dependencies updated and address known vulnerabilities promptly.
- Do not introduce new dependencies with known high-severity CVEs.

## Definition Of Done

- Security-impacting paths include validation and authorization checks.
- No obvious injection, secret exposure, or unsafe deserialization risks are introduced.
- No sensitive data appears in logs, error responses, or serialized output.
