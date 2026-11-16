# Codex Task: Phase 1B Platform Control Plane

# Codex task - Phase 1B, Service 1: Platform Control Plane

You are working in the generic Commerce SaaS Platform monorepo. Read root `AGENTS.md`, `docs/product/PRD.md`, `docs/architecture/PHASE_0_ARCHITECTURE_BASELINE.md`, `docs/architecture/PHASE_1_LOCAL_FOUNDATION.md`, `docs/architecture/OPEN_DECISIONS_REGISTER.md`, ADR-001, ADR-003, ADR-011 and ADR-015, and `backend/services/platform-control-plane/README.md`.

**Precondition:** The user has verified Phase 1A locally and explicitly authorized this task. If not, stop and report the missing precondition.

## Scope - one service only

Implement the first bounded slice of `backend/services/platform-control-plane/`. Do not create or scaffold Identity, Catalogue, Payment, Checkout, other backend services, frontend apps, gateway deployment, Kafka, AI or EC2 resources.

## Required design before code

Before editing, present:
1. Service context, API endpoints and OpenAPI contract proposal.
2. Platform-control DB schema proposal and migration plan.
3. Tenant lifecycle/provisioning state machine.
4. Runtime, migrator, bootstrap and provisioner credential boundaries.
5. Trusted-domain/tenant-context validation approach (local adapter only; no public DNS automation).
6. Threat model and tests.
7. Exact files to create/change and commands to run.

Wait for approval if the proposed design changes any accepted ADR or cannot meet its constraints.

## Initial implementation increments

### Increment A - service scaffold and platform DB
- Independent `pyproject.toml`, `uv.lock`, config, source package, Dockerfile, README and tests.
- FastAPI health/readiness only.
- SQLAlchemy 2 + Psycopg 3 and Alembic for the platform-control database.
- HTTP runtime uses `platform_control_runtime`; the separate provisioning worker uses `platform_control_worker` for job tables and `tenant_database_provisioner` only for DB/role creation; migrations use `platform_control_migrator`. Never configure `local_bootstrap_admin`, worker or provisioner credentials in the HTTP API.
- Pydantic settings validate configuration at startup; no silent default passwords.

### Increment B - tenant registry
- Tenant create/list/get/update lifecycle endpoints with authorization seams, idempotency and audit metadata.
- Tenant slug is not the DB identifier. Use generated opaque tenant IDs.
- Domain registration and verification state; provide only a deterministic local test adapter. Domain must remain unverified until proof is recorded.
- Fail closed for unknown, unverified, suspended, provisioning, offboarding or failed tenants.

### Increment C - provisioning orchestration boundary
- Durable state machine and job records.
- Separate worker entry point/process with the provisioning credential and a distinct low-privilege Control Plane worker DB credential; do not place either credential in the HTTP API app's settings.
- The control-plane DB stores database locator, service name, status and secret reference, never plaintext DB passwords.
- Database provisioning must be idempotent, bounded, recoverable and auditable. Do not implement generic SQL string concatenation from tenant names. The privileged worker creates DBs/roles and persists secret references, but MUST NOT execute Catalogue/Inventory/Orders or any other owning-service migration. Those migrations are run by each owning service using its own migrator credential in its own migration job.
- Create separate service runtime/migrator roles and test credentials cannot access another tenant or another service DB.
- Do not activate a tenant until provisioning, migrations and smoke checks all succeed.

## Mandatory tests

- Unit tests for lifecycle transitions, idempotency and domain normalization.
- Integration tests against local PostgreSQL.
- Migration tests against empty DB and upgrade path.
- Security tests: unknown/suspended/unverified tenant; forged tenant header/body; worker/provisioner credentials not available in API config; runtime credential denied CREATE DATABASE/ROLE; new tenant DB revokes CONNECT/TEMPORARY from PUBLIC; Tenant A cannot connect to Tenant B DB; Catalogue/service role cannot connect to Inventory/service DB.
- Fault injection: provisioning worker restart after each state transition; duplicate jobs; database-create conflict; migration failure; secret-store unavailable; compensation/cleanup state.
- Health/readiness and startup configuration tests.

## Acceptance gate

- Two synthetic tenants can be created.
- Provisioning results in logically separate tenant/service DBs with separate credentials; the fixture service migration runs separately through its owning-service migration runner.
- Platform-control DB contains only platform metadata.
- API runtime uses least-privilege runtime credentials.
- Provisioner runs separately and is not reachable from a public route.
- Unknown, unverified, suspended and incomplete tenants fail closed.
- Migration, API contract, runbook and exact test results are documented.
- Human reviewer understands the provisioning and tenant-resolution code paths and approves the service.

Do not begin Identity & Access or any second service automatically. Stop and provide a completion report with actual test commands/results, known limitations and a plain-language explanation.

---
