# Service change log

## Platform Control Plane, Increment A

- `pyproject.toml`, `uv.lock`: independent locked dependencies and quality tools.
- `Dockerfile`, `.dockerignore`, `.gitignore`: non-root image and local build/tool exclusions.
- `alembic.ini`, `migrations/env.py`: separate migrator identity and migration environment; no revision or tenant tables.
- `src/platform_control_plane/main.py`: application lifecycle, routing, safe errors and request correlation.
- `core/config.py`, `core/logging.py`: validated database settings and structured safe event logs.
- `database/engine.py`, `database/session.py`, `dependencies/database.py`: bounded pool and request session lifecycle.
- `api/routes/health.py`, `api/routes/readiness.py`, `schemas/health.py`: health and readiness contracts.
- `tests/unit/test_foundation.py`, `tests/integration/test_database.py`: configuration, failure, PostgreSQL identity, DDL denial and session checks.
- `README.md`: local operation and boundaries.
- `infra/local/compose.yaml`: opt-in API profile with runtime credential only, localhost port and PostgreSQL health dependency.
- `docs/progress/IMPLEMENTATION_TRACKER.md`, `SERVICE_CHANGELOG.md`, `TEST_RESULTS.md`: review tracking and observed results.
- `migrations/env.py`: revoke the runtime account's inherited privileges on Alembic's version table after online migrations, using the migrator identity; no administrator credential is used.

## Increment B first registry slice

- `tests/security/test_operator_boundary.py`: verify forged identity and forwarding headers cannot bypass the current deny-by-default operator boundary.

- `migrations/versions/001_tenant_registry.py`: approved tenant, idempotency and audit tables with runtime-specific grants.
- `api/routes/tenants.py`, `schemas/tenant.py`, `dependencies/operator.py`, `main.py`: tenant API, validated inputs and fail-closed authorization seam.
- `tests/unit/test_tenants.py`, `tests/integration/test_tenant_registry.py`: deny-by-default and transactional registry tests.
- `README.md`, progress tracker and test results: endpoint behavior, security boundary and actual checks.

## Local Keycloak authentication and platform console

- `infra/local/keycloak/platform-local-realm.json`, `infra/local/compose.yaml`, `scripts/bootstrap_identity.py`: loopback-only Keycloak realm/client/operator bootstrap and selected Compose profiles; no credential values are printed.
- `dependencies/operator.py`, `core/config.py`, `main.py`: OIDC signature/issuer/audience/time/subject validation, `platform-operator` role enforcement and allowlisted console CORS.
- `migrations/versions/003_audit_actor.py`, tenant route/tests: authenticated issuer/subject attribution using the migrator-owned schema change.
- `frontend/apps/platform-console/`: responsive Next.js operator login, tenant list and pending-tenant creation UI.
- `frontend/package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`, `turbo.json`: pinned pnpm/Turborepo workspace and reproducible dependency graph.
- Local end-to-end Authorization Code + PKCE, token claims and authorized tenant API were verified without printing passwords or tokens.
