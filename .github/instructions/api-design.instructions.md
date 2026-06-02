---
description: "REST API conventions, async response patterns, auth contracts, and rate limiting rules. Apply when adding or modifying API endpoints or response schemas."
name: "API Design Conventions"
applyTo:
  - "app/controllers/**/*.py"
  - "app/schemas/**/*.py"
---
# API Design Conventions

## Versioning and URL Structure

- All API routes are prefixed with `/api/v1/`.
- Browser-rendered page routes do not use the `/api/v1/` prefix.
- Use plural resource nouns: `/api/v1/import-files`, `/api/v1/report-runs`, `/api/v1/users`.

## Async Operations

- Long-running operations (file imports, report runs, export generation, CRM syncs) must return `202 Accepted` immediately with a `job_id` in the response body.
- Never block the request thread for operations that may take more than a few hundred milliseconds.
- Provide a `GET /api/v1/<resource>/{job_id}` status endpoint for every async operation so clients can poll for completion.

## Authentication Split

- Browser routes: session authentication + CSRF token on every mutating request.
- API/machine clients: Bearer JWT or hashed personal access token in the `Authorization` header.
- Never mix session cookies and Bearer tokens in the same endpoint's auth logic.

## Rate Limiting

Apply rate limits to the following endpoint categories:

| Endpoint category | Limit (default) |
|---|---|
| Login (`/api/v1/auth/login`) | 10 requests / minute per IP |
| Import upload (`/api/v1/import-files`) | 20 requests / minute per user |
| Export generation (`/api/v1/exports`) | 10 requests / minute per user |
| Webhook receivers (`/api/v1/webhooks/`) | 100 requests / minute per source IP |

## Error Responses

- Never expose stack traces, internal error messages, query details, or file paths in API error responses.
- Return structured JSON errors: `{"error": "<code>", "message": "<human-readable>"}`.
- Use appropriate HTTP status codes: `400` for validation errors, `401` for unauthenticated, `403` for unauthorized, `404` for not found, `422` for unprocessable input, `500` for unexpected server errors.

## Response Contracts

- Validate and serialize all request input and response output through schema classes in `app/schemas/`.
- Never return raw SQLAlchemy model instances directly in responses.

## Definition Of Done

- Every new endpoint has a route test covering the happy path, an unauthorized case (401/403), and at least one invalid input case (400/422).
- Async endpoints return `202` with a `job_id` and have a corresponding status endpoint.
- No internal details leak in error responses.
