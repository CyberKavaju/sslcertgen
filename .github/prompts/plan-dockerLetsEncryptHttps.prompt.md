# Plan: Docker + Let's Encrypt HTTPS Deployment + DNS Wizard Issuance

**TL;DR**: Scaffold a complete Docker deployment for the Flask TLS cert generator and add a guided wizard UX for public certificate issuance. Local dev gets a self-contained Nginx + self-signed cert stack. Production issuance uses Certbot DNS-01 manual challenge. The UI flow becomes: enter domain → get TXT record instructions → verify TXT propagation with a test step → generate certificate only after verification passes → download all certificate artifacts as one ZIP.

---

## Phase 1 — Containerize the Flask App

1. Create `Dockerfile` at project root using a multi-stage Python 3.12 slim build:
   - Stage `builder`: install deps from `requirements.txt` into an isolated prefix
   - Stage `runtime`: copy deps + `app/`, create a non-root user, run Gunicorn on port 8000
2. Create `.dockerignore` at project root: exclude `tests/`, `__pycache__/`, `.env*`, `docs/`, `deployment/`, `.pytest_cache/`, `coverage.xml`

---

## Phase 1.5 — Wizard Feature Architecture (App-Level Changes)

3. Add a dedicated issuance session model in memory (or short-lived store) keyed by a signed `session_id`:
   - `domain`
   - `email`
   - `challenge_name` (for example `_acme-challenge.example.com`)
   - `challenge_value` (TXT token shown to user)
   - `status` enum: `initialized`, `txt_pending`, `txt_verified`, `issuance_running`, `issued`, `failed`
   - timestamps for TTL/cleanup
4. Add backend APIs for wizard steps:
   - `POST /api/v1/public-cert/wizard/start` → validate domain/email and create wizard session
   - `GET /api/v1/public-cert/wizard/<session_id>/txt` → return exact TXT name/value instructions
   - `POST /api/v1/public-cert/wizard/<session_id>/verify-txt` → test DNS TXT propagation and only mark verified if expected token is resolvable
   - `POST /api/v1/public-cert/wizard/<session_id>/generate` → run Certbot only when session status is `txt_verified`
   - `GET /api/v1/public-cert/wizard/<session_id>/download.zip` → return ZIP containing all cert artifacts
5. Add service layer modules for clear separation:
   - `dns_challenge_service.py` for TXT record calculation/instructions and DNS verification
   - `public_cert_wizard_service.py` for state machine and gatekeeping
   - `certificate_bundle_service.py` for ZIP packaging
6. Gate generation with a strict precondition:
   - If TXT verification has not passed in the current session, `/generate` must return `409` with actionable error message and no Certbot execution

---

## Phase 2 — Local Dev Stack (Self-Signed TLS)

7. Create `deployment/nginx/nginx.local.conf`:
   - Port 80 → HTTP redirect to HTTPS
   - Port 443 → TLS with self-signed cert at `/etc/nginx/ssl/{cert,key}.pem`, proxy to `http://app:8000`
   - Sets `X-Forwarded-Proto https` so Flask HTTPS enforcement sees the right scheme
8. Create `deployment/scripts/generate-self-signed.sh`:
   - Runs `openssl req -x509` to generate `cert.pem` + `key.pem` in `/etc/nginx/ssl/` if absent
   - After generation: `chmod 644 cert.pem && chmod 640 key.pem && chown nginx:nginx cert.pem key.pem` so the nginx worker user can read them
9. Create `deployment/docker-compose.yml`:
   - `app` service: build from root `Dockerfile`, env `FLASK_ENV=development`, `HTTPS_ENFORCEMENT_ENABLED=false` (Nginx handles TLS). `HTTPS_ENFORCEMENT_ENABLED` and `HSTS_ENABLED` are existing config flags in `app/config.py`; no code changes needed.
   - `nginx` service: use a custom `deployment/nginx/Dockerfile.local` that extends `nginx:alpine` with `apk add --no-cache openssl` so `generate-self-signed.sh` can run as the entrypoint before nginx starts; mounts `nginx.local.conf` + `ssl-local` named volume
   - Exposes ports `80:80` and `443:443`; ports must be free before starting — the `docker-dev` recipe pre-checks with `ss -ltn | grep -E ':80|:443'` and aborts with an error message if either port is already bound

---

## Phase 3 — Production Stack (Let's Encrypt DNS-01)

10. Create `deployment/nginx/nginx.prod.conf.template`:
   - Port 80 → HTTP redirect (with `server_name ${DOMAIN}`)
   - Port 443 → TLS with LE cert at `/etc/letsencrypt/live/${DOMAIN}/fullchain.pem` + `privkey.pem`
   - TLS protocols: 1.2 + 1.3 only; strong cipher suite; HSTS header
11. Create `deployment/scripts/obtain-le-cert.sh`:
   - Accepts `DOMAIN` and `EMAIL` as args
   - Runs `docker run certbot/certbot certonly --manual --preferred-challenges dns` against the `certbot-certs` named volume
   - Prints clear DNS TXT record instructions; exits with the Certbot output
   - On non-zero Certbot exit, print a remediation hint: `"TXT record verification failed. Check propagation with: dig +short TXT _acme-challenge.${DOMAIN}"` then re-exit with Certbot's original status code
12. Create `deployment/scripts/renew-le-cert.sh`:
   - Runs `docker run certbot/certbot renew` against the same volume
   - Sends `SIGHUP` to the running Nginx container (`docker compose kill -s HUP nginx`) to reload without downtime
13. Create `deployment/docker-compose.prod.yml`:
   - `app` service: same image, env `FLASK_ENV=production`, `HTTPS_ENFORCEMENT_ENABLED=false`, `HSTS_ENABLED=false` (Nginx sets HSTS in header). Both env vars are existing flags in `app/config.py`.
   - `nginx` service: `nginx:alpine`, mounts `nginx.prod.conf.template` at `/etc/nginx/templates/nginx.prod.conf.template` and `certbot-certs` volume at `/etc/letsencrypt`, exposes 80+443
   - Named volume: `certbot-certs` (shared by Nginx and Certbot)
   - **Production bootstrap order**: run `just docker-prod-cert` FIRST to populate the `certbot-certs` volume; if `fullchain.pem` is absent when the nginx container starts, nginx will fail to start — this is intentional fail-fast behaviour; do not start `just docker-prod` before cert issuance succeeds
   - Nginx domain injection: store `nginx.prod.conf` as a template at `deployment/nginx/nginx.prod.conf.template`; the nginx service entrypoint runs `envsubst '$DOMAIN' < /etc/nginx/templates/nginx.prod.conf.template > /etc/nginx/conf.d/default.conf` — the quoted variable list `'$DOMAIN'` ensures only `$DOMAIN` is substituted and all other nginx variables (`$host`, `$remote_addr`, `$uri`, etc.) are preserved verbatim

---

## Phase 3.5 — Wizard UI Flow (TXT-Guided)

14. Replace current one-shot form with a 4-step wizard UI:
    - **Step 1: Domain Input**: ask for domain (and email if required for issuance)
    - **Step 2: DNS TXT Instructions**: display `challenge_name` and `challenge_value` with copy buttons and registrar-agnostic guidance
    - **Step 3: TXT Verification Test**: dedicated "Test TXT Record" action that calls `verify-txt`; show pass/fail status and resolver evidence
    - **Step 4: Generate + Download**: enable "Generate Certificate" only after verification success, then offer "Download ZIP"
15. UX requirements:
    - Step progression is strictly linear; future steps disabled until prior step succeeds
    - Verification failure remains in Step 3 with remediation hints (`dig +short TXT ...`)
    - Preserve wizard state in browser (sessionStorage) and backend (`session_id`) to avoid restart on refresh
    - Display non-secret progress states (`Verifying TXT`, `Issuing Certificate`, `Ready to Download`)
16. ZIP download composition:
    - `fullchain.pem`
    - `privkey.pem`
    - `cert.pem` (if available)
    - `chain.pem` (if available)
    - `README.txt` with install notes and issuance timestamp
    - Optional `metadata.json` (domain, issued_at, expiry)
17. Security and cleanup:
    - ZIP is generated in-memory or in temp dir with immediate cleanup after response
    - `session_id` must be signed and time-limited
    - Rate-limit wizard start/verify/generate endpoints independently to prevent abuse

---

## Phase 4 — Justfile Recipes

18. Add three recipes to `justfile`:
    - `docker-dev`: `docker compose -f deployment/docker-compose.yml up --build`
    - `docker-prod-cert DOMAIN EMAIL`: runs `obtain-le-cert.sh $DOMAIN $EMAIL`
    - `docker-prod DOMAIN`: runs `DOMAIN={{DOMAIN}} docker compose -f deployment/docker-compose.prod.yml up -d`, relying on Docker Compose variable substitution to propagate `DOMAIN` into the nginx service entrypoint and the prod config template

---

## Relevant Files

- `Dockerfile` — create (multi-stage, non-root Gunicorn)
- `.dockerignore` — create
- `deployment/docker-compose.yml` — create (local dev stack)
- `deployment/docker-compose.prod.yml` — create (production LE stack)
- `deployment/nginx/nginx.local.conf` — create
- `deployment/nginx/nginx.prod.conf.template` — create (template; `$DOMAIN` substituted at container startup via `envsubst '$DOMAIN'`)
- `deployment/scripts/generate-self-signed.sh` — create
- `deployment/scripts/obtain-le-cert.sh` — create (DNS-01 certbot runner)
- `deployment/scripts/renew-le-cert.sh` — create (certbot renew + nginx reload)
- `justfile` — extend with 3 new recipes
- `app/controllers/public_cert_wizard_controller.py` — create (wizard endpoints)
- `app/services/public_cert_wizard_service.py` — create (wizard state machine)
- `app/services/dns_challenge_service.py` — create (TXT verify logic)
- `app/services/certificate_bundle_service.py` — create (ZIP artifact builder)
- `app/views/certificate/index.html` — update to 4-step wizard UX
- `app/static/js/certificate_page.js` — update for step navigation, verification gate, and ZIP download
- `tests/integration/test_public_cert_wizard_controller.py` — create
- `tests/unit/services/test_public_cert_wizard_service.py` — create
- `tests/unit/services/test_dns_challenge_service.py` — create
- `tests/unit/services/test_certificate_bundle_service.py` — create

---

## Verification

1. `just docker-dev` → Nginx starts with self-signed cert; `curl -k https://localhost/healthz` returns `{"status": "ok"}`
2. `curl -k -X POST https://localhost/api/v1/generate -H 'Content-Type: application/json' -d '{"domain":"test.example.com"}'` returns PEM cert + key
3. Check nginx logs: `docker compose -f deployment/docker-compose.yml logs nginx` — no errors
4. For production: `just docker-prod-cert yourdomain.com admin@yourdomain.com` → add TXT record → Certbot confirms cert issued to `certbot-certs` volume
5. `DOMAIN=yourdomain.com just docker-prod` → `curl https://yourdomain.com/healthz` returns green LE cert (no `-k` needed)
6. Wizard happy path test:
   - Start wizard with domain/email
   - Confirm TXT instructions render in UI
   - Add TXT record in DNS
   - Click "Test TXT Record" and verify backend returns `verified=true`
   - Click "Generate Certificate" and verify issuance completes
   - Download ZIP and confirm it includes expected PEM files
7. Wizard negative-path tests:
   - Wrong/missing TXT record keeps session at `txt_pending`
   - `/generate` before verify returns `409`
   - Expired/invalid `session_id` returns `401/404`

---

## Decisions

- **DNS-01 manual** — no automated DNS API needed; user adds `_acme-challenge` TXT record once during issuance and again for each renewal
- **Nginx handles TLS termination** — Flask app always runs plain HTTP on 8000 internally; `X-Forwarded-Proto` is set so Flask headers (HSTS etc.) remain configurable per environment
- **Wizard-first issuance UX** — certificate generation is no longer one-shot for public cert flow; it is gated by TXT verification in the app UI and API
- **Excluded**: HTTP-01 challenge support, automated renewal cron (manual `renew-le-cert.sh`), Kubernetes/Helm configs

---

## Further Considerations

1. **Cert renewal frequency** — LE certs expire every 90 days. DNS-01 manual renewal requires human action to add the TXT record each time. Consider switching to a DNS provider with an API later (Cloudflare plugin: `certbot-dns-cloudflare`) for fully automated `certbot renew` via cron.
2. **DOMAIN env var injection into Nginx** — the entrypoint runs `envsubst '$DOMAIN' < template > /etc/nginx/conf.d/default.conf`. `gettext` (which provides `envsubst`) must be installed: add `apk add --no-cache gettext` to the nginx service's Dockerfile or `command` override. Quoting `'$DOMAIN'` is mandatory to prevent envsubst from clobbering nginx's own `$variable` syntax.
