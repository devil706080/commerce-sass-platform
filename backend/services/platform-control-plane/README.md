# Platform Control Plane

## Purpose
Own SaaS-level tenant registry and lifecycle, verified domain mappings, plan/entitlement metadata, provisioning orchestration records and database/secret references. This service does not own tenant commerce data.

## Data ownership
Singleton `platform_control` database only. Never store tenant products, customer profiles, carts, inventory, orders, payment transactions or provider secrets in plaintext here. Store opaque secret references only.

## Process boundaries
- HTTP API: tenant registry/domain/lifecycle operations, least-privilege `platform_control_runtime` DB role.
- Migration runner: this service's Alembic migrations, `platform_control_migrator` role.
- Provisioning worker: reads/writes only authorized provisioning-job rows using `platform_control_worker`; database/role creation uses a separate privileged credential supplied only to that isolated worker. No public route can call arbitrary SQL/provisioning commands.
- The worker creates tenant/service databases, roles and secret references. It MUST NOT run Catalogue/Inventory/Orders or any other owning-service migrations. Each owning service runs its own migration job using its own migrator.

## First implementation increments
1. Health/readiness and validated configuration.
2. Control-plane schema and migrations.
3. Tenant registry with lifecycle state machine and audit metadata.
4. Domain registration/verification state using a deterministic local test adapter only.
5. Durable provisioning job state and worker boundary.
6. Two-tenant provisioning proof and negative credential tests.

## Security invariants
- Tenant context derived from trusted ingress + verified domain lookup.
- Browser-supplied tenant IDs are never database-routing authority.
- Verify signed internal context issuer, audience, expiry, key ID/signature and tenant lifecycle.
- Tenant DB access denied by default; revoke `CONNECT`/`TEMPORARY` from `PUBLIC`.
- Runtime role cannot create databases/roles or apply DDL. Provisioner credential is never loaded by the HTTP API.
- Provisioning is idempotent, bounded, auditable and recoverable.

## Required tests
See `docs/agent-prompts/PHASE_1B_PLATFORM_CONTROL_PLANE.md` for full entry, exit, failure-injection and tenant-isolation criteria.
