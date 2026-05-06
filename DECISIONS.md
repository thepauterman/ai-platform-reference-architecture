# Architecture Decision Log

This document records key architectural decisions made during the build of the AI Governance Gateway. Each entry captures the context, the options considered, and the rationale for the choice made.

---

## ADR-001: FastAPI over Flask for the gateway service

**Date:** 2026-03  
**Status:** Accepted

**Context**  
Needed a Python web framework to serve as the gateway API layer.

**Options considered**  
- Flask — lightweight, widely used, simple
- FastAPI — async-native, automatic OpenAPI docs, type validation via Pydantic
- Django — full-featured but heavyweight for an API-only service

**Decision**  
FastAPI. The automatic request/response validation via Pydantic models, built-in OpenAPI docs at `/docs`, and async support made it the right fit for a production-grade API gateway.

---

## ADR-002: Regex-based PII detection over Presidio

**Date:** 2026-03  
**Status:** Accepted, revisit in Phase 12

**Context**  
Needed PII detection before prompts reach model providers.

**Options considered**  
- Microsoft Presidio — production-grade NLP-based PII detection
- Regex patterns — simple, fast, no dependencies
- AWS Comprehend — managed NLP service

**Decision**  
Regex for the prototype phase. Presidio was noted as the preferred production approach but adds significant dependency weight and setup complexity. The regex patterns cover the core PII types (EMAIL, SSN, PHONE, CREDIT_CARD) sufficient for a governance prototype. Presidio is the planned upgrade in a future hardening phase.

---

## ADR-003: Cloud Run over GKE for compute

**Date:** 2026-03  
**Status:** Accepted

**Context**  
Needed a compute platform to run the gateway service on GCP.

**Options considered**  
- GKE (Google Kubernetes Engine) — full Kubernetes, maximum control
- Cloud Run — fully managed, scales to zero, container-native
- Compute Engine — raw VMs, maximum flexibility

**Decision**  
Cloud Run. For a prototype and early production service, the operational overhead of managing Kubernetes is not justified. Cloud Run provides automatic scaling, zero-downtime deploys, and native GCP integration with minimal configuration. GKE becomes relevant if the platform needs to run multiple services with complex networking requirements.

---

## ADR-004: Firestore over SQLite for production audit logging

**Date:** 2026-04  
**Status:** Accepted

**Context**  
The audit logger initially used SQLite for local development. Needed a production-grade backend.

**Options considered**  
- SQLite — simple, file-based, no infrastructure needed
- Firestore — managed NoSQL, scales automatically, native GCP integration
- BigQuery — best for analytics, overkill for operational audit logs
- Cloud SQL (PostgreSQL) — relational, requires instance management

**Decision**  
Firestore for production, SQLite retained for local development. The dual-backend pattern (`AUDIT_BACKEND` env var) means developers can run locally without GCP credentials while production uses a managed, scalable store. Firestore's document model maps naturally to audit log entries and requires zero infrastructure management.

---

## ADR-005: API key authentication over OAuth / GCP IAM

**Date:** 2026-04  
**Status:** Accepted, revisit for multi-tenant

**Context**  
Needed to secure the gateway API endpoints in production.

**Options considered**  
- GCP IAM Bearer tokens — native GCP auth, requires GCP identity
- API key via header — simple, portable, works from any client
- OAuth 2.0 — full identity management, significant complexity
- No auth — acceptable for prototype only

**Decision**  
API key via `X-API-Key` header, stored in GCP Secret Manager. Simple enough to implement in one phase, sufficient for a single-tenant production deployment. OAuth or GCP IAM-based auth is the right upgrade path when the platform needs to support multiple tenants or user identities.

---

## ADR-006: Multi-provider routing by request classification

**Date:** 2026-03  
**Status:** Accepted

**Context**  
Needed a strategy for selecting which LLM provider handles each request.

**Options considered**  
- Always use one provider — simple but no cost or capability optimisation
- Random load balancing — distributes load but ignores capability differences
- Classification-based routing — match request complexity to provider capability

**Decision**  
Classification-based routing. Requests are classified as simple, standard, or complex based on prompt content and length. Complex requests route to Anthropic (strongest reasoning), standard to OpenAI (balanced), simple to Vertex AI (lowest cost). This pattern reflects how real enterprise AI platforms manage cost vs capability tradeoffs.

---

## ADR-007: GitHub Actions for CI/CD over Cloud Build

**Date:** 2026-04  
**Status:** Accepted

**Context**  
Needed a CI/CD pipeline to automate builds and deployments on push to main.

**Options considered**  
- Google Cloud Build — native GCP, integrates directly with Artifact Registry
- GitHub Actions — lives alongside the code, widely understood
- Manual deploy scripts — no automation, error-prone

**Decision**  
GitHub Actions. Keeping the pipeline definition in the same repository as the code (`.github/workflows/deploy.yml`) makes the deployment process transparent and version-controlled. Cloud Build is a valid alternative but adds another GCP service to manage. The workflow authenticates to GCP via a service account key stored as a GitHub secret.

---

## ADR-008: Terraform for infrastructure over manual GCP console

**Date:** 2026-03  
**Status:** Accepted

**Context**  
Needed to provision and manage GCP infrastructure.

**Options considered**  
- GCP Console (manual) — fast to start, not reproducible
- Terraform — infrastructure as code, reproducible, version-controlled
- Pulumi — code-based IaC, steeper learning curve
- gcloud CLI scripts — reproducible but not declarative

**Decision**  
Terraform. Infrastructure as code ensures the environment is reproducible, auditable, and can be torn down and rebuilt from scratch. All GCP resources (Cloud Run, Artifact Registry, Secret Manager, IAM, Firestore) are defined in `infra/` and version-controlled alongside the application code.

---

## ADR-009: Vite + React + TypeScript for the control plane UI, served from FastAPI

**Date:** 2026-05  
**Status:** Accepted

**Context**  
Phase 10 added a real-time dashboard that visualises the gateway pipeline, audit log, and aggregated metrics. We needed both a frontend stack and a deployment model that fits a single-service Cloud Run target.

**Options considered**  
- **Frontend stack** — Server-rendered Jinja templates (simple, but no client-side animation), Next.js (full-stack but heavyweight for a dashboard that only consumes existing APIs), Vite + React + TypeScript (fast HMR, single-page bundle, type safety end-to-end).
- **Deployment** — Two services (separate static-hosting bucket + Cloud Run for the API, requires CORS and a second deploy target), single multi-stage container (Node builds the bundle, Python serves it as static files, one image and one Cloud Run service).

**Decision**  
Vite + React + TypeScript, packaged with the backend in a single multi-stage container served by FastAPI's `StaticFiles`. The UI calls the API on the same origin, eliminating CORS in production. CI/CD stays a single `docker build` + `gcloud run deploy`. `VITE_API_KEY` is passed as a build-arg so it lives in the bundle the same way `GATEWAY_API_KEY` lives in Secret Manager — acceptable for a single-tenant deployment; the right upgrade path for multi-tenant is a session-cookie auth flow that doesn't bake credentials into the bundle.