# Executive Summary  
This PRD outlines a Dockerized Python web application that lets a user enter a domain name and receive a TLS certificate and private key. The implementation standard for this project is Python 3.12+, with a lightweight web framework (FastAPI or Flask) and Python-native cryptography libraries. Python is selected for maintainability, rapid development, strong testing/tooling support, and a mature X.509 ecosystem centered on the `cryptography` package【54†L49-L58】. While Python does not target the raw throughput of compiled stacks in benchmark-heavy scenarios【13†L213-L221】【13†L290-L293】, it is fully sufficient for this product’s expected load profile when deployed with a production ASGI/WSGI server and horizontal scaling.  

Key requirements include secure, in-memory key handling, HTTPS for all UI/API traffic, domain validation, and abuse protection (e.g. rate limits, since Let’s Encrypt limits issuance to ~50 certs/domain/week). For public website use, the product must support a browser-trusted CA-signed certificate path so generated output does not trigger browser security warnings; self-signed certificates are acceptable only for local development, testing, or explicitly non-public use. The UI will be a simple single-page form (or server-rendered page) with domain input and “copy certificate/key” buttons (using the Clipboard API). Optionally the cert and key can be offered as downloadable text files. We will build Docker images using Python multi-stage patterns and slim runtime images to minimize size and attack surface, and configure CI/CD (e.g. GitHub Actions) to test and deploy the container. Below we detail functional and non-functional requirements, user stories, data flow and threat model, API design, diagrams, testing/monitoring plan, and a sprint-based timeline. Citations reference authoritative sources where available.  

## Functional Requirements  
- **Domain Input & Validation:** User enters a valid FQDN. The app must validate format (and optionally check DNS availability), rejecting invalid input.  
- **Certificate Generation:** Upon valid request, the backend generates an X.509 certificate and private key for that domain. Options: self-signed, using an internal CA, or using a publicly trusted CA workflow. For public-facing deployments, the product must support a browser-trusted CA-signed certificate path so installed certificates do not produce browser trust warnings. Libraries/tools should use Python-native options first (`cryptography`, `acme`, `certbot` integrations) and optionally OpenSSL CLI as a controlled fallback【54†L49-L58】.  
- **Output Delivery:** The UI displays the PEM-formatted certificate and private key in separate text areas. Users can copy text to clipboard (via the JavaScript Clipboard API【64†L227-L235】) or download each as a file (e.g. `.pem`). Buttons or links should facilitate “Copy” and “Download” functions.  
- **Accessibility & Feedback:** Provide immediate feedback on errors (invalid domain, rate limit exceeded, etc.) and confirm success. The UI should be responsive (mobile-friendly) but is essentially a one-page form (no complex multi-page flows needed).  

## Non-Functional Requirements  
- **Performance:** The service should handle multiple simultaneous requests with low latency. The Python service should target practical product throughput (e.g. 100+ RPS baseline under normal request mix), with acceptable response time (<1s median per certificate) and clear scaling guidance via multiple container replicas.  
- **Scalability:** Container design allows horizontal scaling (multiple instances behind a load-balancer if needed). The app should not assume a fixed domain list.  
- **Security:** All traffic to/from the app must use HTTPS (the app can be run behind an SSL-terminating reverse proxy or have TLS built-in). Private keys must never be persisted or logged on disk; handle them only in memory and clear buffers immediately after use. Use secure random generators and trusted libraries. Validate inputs to prevent injection attacks. Protect against brute-force or denial-of-service by implementing rate limiting (e.g. max X requests per minute per IP) and CAPTCHAs if necessary. Ensure third-party libraries (e.g. crypto libs) are up to date to avoid known vulnerabilities. For public website usage, certificate issuance and deployment must avoid self-signed output unless the browser trust chain is explicitly established by an installed trusted root.  
- **Docker Compliance:** The service must run as a standalone Docker container. Use official minimal Python base images (e.g. `python:3.12-slim`) and multi-stage builds to keep images small【29†L1000-L1008】. The container should drop root privileges and run as an unprivileged user if possible. Configuration (e.g. rate limits, CA certs) should be via environment variables or mounted volumes, not hard-coded.  
- **Logging & Monitoring:** Log all certificate requests (timestamp, domain, success/failure) in structured logs (JSON) without including the private key. Implement basic metrics (counts of successes/failures, latencies). Provide hooks for container orchestration health checks (e.g. `/healthz` endpoint).  
- **Compliance:** If integrating with a CA like Let’s Encrypt, ensure compliance with their policies (e.g. rate limits【24†L134-L140】). Avoid storing user data. If the app is public-facing, include terms-of-service disclaimers (especially if using LE, the user must verify domain control in production use).

## User Stories & Acceptance Criteria  
- **Story 1:** *“As a user, I want to enter a domain name and instantly receive a valid certificate and key so that I can use them for my site.”*  
  - Acceptance: Entering `example.com` generates two text blocks: one PEM certificate and one PEM key. Both can be copied or downloaded. A success message appears.  
- **Story 1a:** *“As a user deploying a public website, I want the certificate flow to produce browser-trusted certificates so visitors do not see certificate warnings.”*  
  - Acceptance: In production/public mode, the certificate workflow uses a publicly trusted CA path or equivalent trusted deployment path, and the resulting site certificate validates in standard browsers without trust warnings.  
- **Story 2:** *“As a user, I want invalid input to be rejected, so that I know why the request failed.”*  
  - Acceptance: Entering invalid domains (e.g. `-invalid`) shows an error without app crash.  
- **Story 3:** *“As an operator, I want requests and errors to be logged, so I can audit usage and troubleshoot issues.”*  
  - Acceptance: Logs show timestamp, client IP, domain requested, and status. No sensitive data (e.g. private key) is logged.  
- **Story 4:** *“As a user, I expect the app to remain responsive under load, so it does not hang or crash.”*  
  - Acceptance: Under simulated high load (e.g. 100 RPS), the average response time remains under 1-2 seconds.  

## Data Flow and Threat Model  
The basic data flow is: **User (Browser)** ⇄ **WebApp/API** ⇄ **Certificate Generator**. The sequence is illustrated below. Input data (domain) flows from the client to the server. The server validates it, then invokes a crypto library or CLI (e.g. OpenSSL) to generate a certificate and key. The key material is returned to the server (in-memory) and then delivered to the client over HTTPS. 

Key threats include:
- **Input Abuse:** A malicious user might supply a very long or special-character domain to attempt buffer overflow or command injection. *Mitigation:* Rigorously validate domain syntax (length limits, allowed characters), and if using system calls, safely escape arguments or use library functions instead.
- **Denial of Service (DoS):** Attackers could flood requests to exhaust CPU or memory. *Mitigation:* Implement rate-limiting per IP/account. (Public CAs also have rate-limits【24†L134-L140】).
- **Data Exposure:** The private key is highly sensitive. *Mitigation:* Do not log or store the private key; generate it only in memory. Use secure OS/crypto APIs (e.g. lock pages, zero memory on drop). For maximum security, one could use an HSM, but for this app, ensure server memory is properly managed.
- **Man-in-the-Middle (MitM):** If the web app were accessed over HTTP, an attacker could steal certificates. *Mitigation:* Enforce HTTPS (e.g. require TLS for the web app itself) and use HSTS.  
- **Vulnerable Libraries:** Using outdated crypto libs could introduce CVEs. *Mitigation:* Use well-maintained Python libraries (especially `cryptography`) and keep dependencies and base images up to date.

**Mermaid Sequence Diagram:**  
```mermaid
sequenceDiagram
  participant User as User (Browser)
  participant API as WebApp/API
  participant Gen as CertGenerator
  User->>API: GET / (load UI)
  User->>API: POST /generate {domain: "example.com"}
  API->>API: validateDomain("example.com")
  alt valid domain
    API->>Gen: generateCert("example.com")
    Gen-->>API: {certPEM, keyPEM}
    API-->>User: HTTP 200 {certificate, key}
  else invalid
    API-->>User: HTTP 400 {"error": "Invalid domain"}
  end
```

## API Design and Endpoints  
- **GET /** – Returns the HTML/JS UI (one page with a domain input and buttons).  
- **POST /generate** – Accepts JSON or form data `{ "domain": "example.com" }`. The response is JSON containing `{ "certificate": "<PEM string>", "key": "<PEM string>" }` on success (HTTP 200), or an error message (HTTP 400/429/500) on failure.  
- **GET /healthz** – Returns 200 OK if the app is running (for container health checks).  
Sample API contract (JSON): 
```json
POST /generate
Request:  { "domain": "example.com" }
Response: { "certificate": "-----BEGIN CERT...END CERT", "key": "-----BEGIN PRIVATE KEY...END KEY" }
```

**Endpoints:** No external APIs are strictly required for the self-signed MVP. For production/public browser-trusted certificates, the product should support a CA-backed issuance path such as Let’s Encrypt via a Python ACME client (e.g. `acme`/Certbot libraries) or an equivalent reverse-proxy-managed certificate flow.

## Architecture Diagram  
【49†embed_image】 *Illustrative architecture: the web container handles HTTPS requests, validates input, generates cert/key, and returns them to the client. Key generation is done in-memory, with no persistent storage of secrets.*  

The app will be containerized (Docker). It may run behind a reverse proxy (e.g. Nginx) to terminate TLS on the public interface, routing requests to the container. Internally, the Python web app (FastAPI or Flask) calls Python certificate libraries or executes OpenSSL in a safe, parameterized manner. All config (rate limits, any CA keys, etc.) is externalized.

## Python Stack Profile  

| **Component** | **Primary Choice** | **Notes** |
|---|---|---|
| Runtime | Python 3.12+ | Stable ecosystem and strong packaging/tooling support |
| Web Framework | FastAPI (default) or Flask | FastAPI for typed APIs and async support; Flask for minimal synchronous architecture |
| Crypto/X.509 | `cryptography` | Primary library for keypair generation and certificate building【54†L49-L58】 |
| Optional ACME | Python `acme` / Certbot integration | Adds production CA issuance flows with domain validation |
| App Server | Uvicorn/Gunicorn | Production process model with worker tuning |
| Validation | Pydantic (FastAPI) or WTForms/manual validators (Flask) | Enforce strict FQDN checks and request schemas |
| Rate Limiting | Flask-Limiter or SlowAPI | Per-IP throttling and abuse controls |
| Container Base | `python:3.12-slim` | Small runtime image with multi-stage build support |
| Testing | Pytest + integration tests | Validate X.509 content, domain validation, and endpoint behavior |

This profile standardizes implementation decisions around Python only, balancing delivery speed, security, and operational simplicity for this product.

## Libraries & Certificate Generation  
- **Python (`cryptography`):** Primary library for X.509 building/signing and private key generation in Python services【54†L49-L58】.  
- **Python ACME Tooling (`acme` / Certbot APIs):** For optional Let’s Encrypt integration and CA-compliant issuance workflows.  
- **OpenSSL CLI (fallback):** Optional fallback path when operational requirements demand direct CLI compatibility; must be invoked safely with strict argument handling.  

## UX/UI Considerations  
The UI is very simple: a form with a single input for the domain and a “Generate” button. Upon success, two large readonly text areas appear (one for the cert, one for the key), each with a “Copy” button. Optionally a “Download” button can trigger a download of the PEM text as a file. We can implement copy via the [Clipboard API](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText)【64†L227-L235】. Since there’s minimal navigation, this could be a small single-page app (React/Vue) or even a server-rendered template with a bit of JS. A responsive design is recommended so mobile users can use it. No authentication is assumed (public utility); if it were private, one could add login later.  

## Security & Compliance  
- **Key Handling:** Generate keys in-memory and immediately hand them to the user. Do not write to disk or log them. Use Python secure RNG primitives and trusted cryptographic backends. Consider libraries/utilities that reduce key material lifetime in memory.  
- **TLS for the App:** The web app itself should run under HTTPS (even if generating certificates, to protect the private key on the wire). For local testing, a self-signed cert or dev-tools can be used. For public-facing usage, the certificate presented to browsers must chain to a trusted public root or another trust anchor already distributed to clients.  
- **Rate Limiting:** Prevent abuse by limiting how often a client can generate certs. Let’s Encrypt’s published limits (50 certs/week/domain【24†L134-L140】) serve as a guide; even if we self-sign, some abuse vector may exist (e.g. DoS). Implement a throttling mechanism (e.g. no more than X requests/minute per IP).  
- **Input Validation:** Strictly validate the domain string (regex for valid hostnames, length limits). Reject inputs that could break DNS norms or include shell metacharacters.  
- **Updates & Patches:** Use well-maintained Python libraries and subscribe to CPython and dependency security advisories. Keeping Python base Docker images (e.g. slim variants) updated is crucial.  
- **Compliance:** If using Let’s Encrypt or acting as a CA, abide by their terms (e.g. domain validation rules). If intended for enterprise use, ensure any data logging complies with privacy policies (we store essentially only domain names, which are not PII).  

## Testing, Logging, and Monitoring  
- **Unit/Integration Tests:** Write tests for domain validation logic, and for the certificate generation routine (e.g. verify that the generated cert’s subject matches the input domain). Automated tests can use a test CA or mock the crypto calls.  
- **Load Testing:** Use tools (e.g. `hey`, `ab`) to simulate concurrent requests and ensure performance targets.  
- **Logging:** As noted, log each request in JSON with fields: `{ timestamp, clientIP, domain, status }`. Log errors with a stack trace (if in dev mode) or error code. Use structured Python logging libraries (e.g. stdlib `logging` with JSON formatter, `structlog`, or `loguru`).  
- **Monitoring:** Expose basic metrics, e.g. a Prometheus `/metrics` endpoint if needed, counting total requests, successful generations, error counts, and average latencies. Docker/CNI metrics or simple logs can feed into a monitoring solution.  
- **Compliance Auditing:** Keep an audit log of certificates generated if needed (the CSR/subdomain info) but *never* log the private key. If using a CA approach, record certificate serials.

## Deployment & CI/CD  
Use a Git-based workflow (GitHub/GitLab). On each commit to `main`, run CI that: lints code, runs unit tests, builds a Docker image (multi-stage to reduce size【29†L1000-L1008】), and optionally pushes to a container registry. CD pipeline should pull the image onto the target server (any cloud VM or Kubernetes cluster) and run it, replacing the old container.  

**Example GitHub Actions steps:** (adapted from【31†L143-L152】)  
```yaml
- uses: actions/checkout@v3
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
- name: Install dependencies and run tests
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pytest -q
- name: Build Docker image
  run: docker build -t mycertapp:${{ github.sha }} .
- name: Publish to Registry
  run: docker push myregistry/mycertapp:${{ github.sha }}
- name: Deploy
  uses: appleboy/ssh-action@v1
  with:
    host: ${{ secrets.HOST }}
    script: |
      docker pull myregistry/mycertapp:${{ github.sha }}
      docker stop certapp || true
      docker rm certapp || true
      docker run -d --name certapp -p 443:443 myregistry/mycertapp:${{ github.sha }}
```
This workflow builds and deploys on push to `main`. In a production environment, replace SSH with your orchestration method (Kubernetes `kubectl`, AWS ECS, etc).

## Milestones & Timeline  
The project can be divided into agile sprints. A sample 2-week sprint schedule is shown below.  

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title Project Timeline (Example)
    section Sprint 1: Planning & Design
      Research requirements & architecture        :active, 2026-06-03, 2w
      Define stack and tools                      :2026-06-03, 1w
    section Sprint 2: Backend Core
      Develop API endpoints & cert generation    :2026-06-17, 2w
      Implement domain validation                :2026-06-17, 1w
    section Sprint 3: Frontend UI
      Build web form and interactions            :2026-07-01, 2w
      Integrate copy/download functionality      :2026-07-08, 1w
    section Sprint 4: Security & Hardening
      Add HTTPS, rate-limiting, input sanitization:2026-07-15, 2w
      Threat model testing (fuzz inputs)         :2026-07-22, 1w
    section Sprint 5: Testing & Logging
      Write unit/integration tests               :2026-07-29, 1w
      Implement logging and monitoring           :2026-07-29, 1w
    section Sprint 6: CI/CD & Deployment
      Setup Docker builds & CI pipeline          :2026-08-05, 1w
      Deploy to staging & review                 :2026-08-05, 1w
    section Release
      Final QA & Launch                          :2026-08-12, 1w
```  
Each bullet is an example effort (total ~10 weeks). Adjust durations as needed. 

## Recommended Stack and Rationale  
Based on the above analysis, a **Python-based stack** is recommended for production in this project: it provides the best balance of implementation speed, ecosystem maturity, and operational simplicity for a certificate-generation utility. The server should use FastAPI (preferred) or Flask, with `cryptography` for certificate generation/signing【54†L49-L58】 and optional Python ACME tooling for future Let’s Encrypt integration. Python container images remain straightforward to build and deploy with multi-stage Docker practices【29†L1000-L1008】. For the UI, a minimal HTML+JS frontend (no heavy framework needed) is sufficient. This approach prioritizes maintainability, testability, and clear security controls while still meeting target traffic requirements through worker tuning and horizontal scaling. 

**Sources:** TechEmpower benchmarks【13†L213-L221】【13†L290-L293】 provide performance context. Docker best practices【29†L1000-L1008】 inform the container design. `cryptography` docs【54†L49-L58】 confirm Python X.509 capabilities. Let’s Encrypt’s limits【24†L134-L140】 underscore the need for rate limiting. The CI/CD example【31†L143-L152】 illustrates how to automate building and deployment. All recommendations are derived from these authoritative sources.

## Phase 0 Binding Defaults (Confirmed 2026-06-02)
- Framework: Flask.
- Certificate mode for MVP: self-signed only.
- Production/public requirement beyond MVP: support a browser-trusted CA-signed certificate path.
- Deployment target: single Docker container behind reverse proxy.
- Phase 0 scope rule: record decision defaults and scaffold/config/quality foundations only.
- Explicitly out of Phase 0 scope: certificate-generation modules and API business logic.

## Phase 3.4 TLS, Proxy Trust, and Security Headers (Implemented Strategy)

### Deployment Trust Model
- Traffic path: client -> TLS terminator/reverse proxy -> Flask app.
- Reverse proxy is the HTTPS boundary in production and must forward trusted headers.
- Flask trusts forwarded client metadata with a bounded hop count via `TRUST_PROXY_HOPS` (default `1`).
- Assumption: only trusted infrastructure can set `X-Forwarded-For` and `X-Forwarded-Proto`.

### HTTPS Enforcement Responsibility Split
- Proxy responsibility (primary): terminate TLS and redirect cleartext HTTP to HTTPS.
- App responsibility (defense in depth): optional request rejection when `HTTPS_ENFORCEMENT_ENABLED=true`.
- Current app default keeps enforcement off to avoid breaking local/dev proxy setups unexpectedly.

### Security Header Policy (App Baseline)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`
- `Strict-Transport-Security` is conditional (`HSTS_ENABLED=true`) and emitted only on secure requests.

### Operational Verification Checklist (Phase 6 Ready)
1. Verify proxy forwards client and proto headers as expected:
  - `curl -i https://<host>/healthz`
  - Confirm app response is `200` and includes baseline security headers.
2. Verify HTTP->HTTPS behavior at proxy layer:
  - `curl -i http://<host>/healthz`
  - Confirm redirect or policy-compliant rejection by deployment setup.
3. Verify HSTS behavior after enabling `HSTS_ENABLED=true`:
  - `curl -i https://<host>/healthz`
  - Confirm `Strict-Transport-Security` appears with configured directives.
4. Verify rate-limit client identity honors trusted proxy hops:
  - Send requests with distinct `X-Forwarded-For` values through trusted proxy path.
  - Confirm per-IP throttling is isolated per client IP.
5. Verify payload/body limits in deployment mode:
  - Send body larger than `MAX_CONTENT_LENGTH` and confirm structured `413` response.