# Test results

2026-11-16, Platform Control Plane Increment A:

- `uv lock --check`: passed, 38 dependencies resolved.
- `uv run ruff check src tests migrations`: passed.
- `uv run ruff format --check src tests migrations`: passed.
- `uv run mypy src`: passed, 10 source files.
- `uv run pytest tests/unit -q`: 6 passed; FastAPI/Starlette emitted an httpx deprecation warning.
- Initial `RUN_DB_INTEGRATION=1 uv run pytest tests/integration -q`: 2 passed against local PostgreSQL, same warning. Runtime CREATE TABLE was denied.
- After adding a migration-history privilege assertion, the initial run had 7 passed, 1 failed because runtime inherited UPDATE on `public.alembic_version`. After owner authorization, `uv run alembic upgrade head` executed the migrator-owned permission safeguard; `uv run pytest -q` with integration enabled then passed all 8 tests. No new migration revision was applied.
- `uv run alembic upgrade head`: exited successfully with migrator credentials and no revision scripts. It created the migrator-owned `public.alembic_version` table.
- Host Uvicorn smoke test on loopback port 18089: `/health` and `/ready` both returned `ok`; process stopped afterward.
- Updated Compose configuration validation with `--env-file .env` and `--profile platform-control`: passed.
- `docker compose --env-file .env -f infra/local/compose.yaml --profile platform-control up -d --build platform-control`: image built and container started. Compose reports healthy and loopback port 8000; HTTP `/health` and `/ready` returned `ok`.

No vulnerability scan, empty-database migration test, or full privilege/security audit has been run.

## Increment B first slice

- Approved `001_tenant_registry` migration rendered and applied with `platform_control_migrator`.
- `uv run ruff check src tests migrations`, `uv run ruff format --check src tests migrations`, and `uv run mypy src`: passed.
- `RUN_DB_INTEGRATION=1 uv run pytest -q`: 10 passed, one Starlette/httpx deprecation warning. Registry integration uses a rolled-back transaction and a test-only authorization override; default routes deny callers.
- Rebuilt Docker Compose service: container healthy, `/health` and `/ready` returned `ok`, and unauthenticated `GET /api/v1/tenants` returned 403. Docker reported a 333 MB image; the replaced image was no longer present after Compose recreated the container.
- No production authentication, operator actor attribution, concurrency stress test, vulnerability scan, or migration downgrade test was performed.

Duplicate-name change (pending migration approval): Ruff lint and format check, MyPy and 7 unit tests passed. The new duplicate integration assertion has not run because revision `002_unique_tenant_name` is not applied. The running container still has the previous implementation.

Local label preview: Ruff lint and format check, MyPy and 10 unit tests passed, including local mapping, unknown-host denial, production disabling and 403 tenant-route checks. A separate host-process HTTP smoke attempt failed to start/respond and the cause was not established; no successful browser or container smoke test is claimed. The running container has not been rebuilt with this change.

Follow-up: owner-approved migration `002_unique_tenant_name` applied using the migrator; full suite passed 13 tests (one Starlette/httpx deprecation warning). The image rebuilt and the Docker-hosted local preview returned `Example Store`; readiness returned `ok`. The previous host-process smoke attempt remains unexplained.

Authorization-boundary regression: `uv run pytest tests/unit tests/security -q` passed 11 tests (one Starlette/httpx deprecation warning). Forged bearer tokens, tenant headers and forwarded host headers did not unlock create, list or get operations. This verifies denial only; operator authentication is not implemented.

OIDC work in progress: a first signature, issuer, audience, expiry and operator-role validation path was added; `uv run pytest tests/unit tests/security -q` passed 12 tests, Ruff and MyPy passed. Tests use generated test keys and a mocked key endpoint; this is not a Keycloak end-to-end test. Keycloak is not started or configured, actor audit attribution and role granularity are not implemented, and the running container was not rebuilt. The auth implementation is not ready for production or for enabling tenant routes.

Follow-up: migration `003_audit_actor` was applied with owner authorization via `platform_control_migrator`. New tenant audit events now record the issuer and subject returned by validated operator-token handling; existing audit records remain null. Full suite: 15 passed, with one Starlette/httpx deprecation warning; Ruff and MyPy passed. Tests use mocked identity and do not verify a real Keycloak login. The running container has not been rebuilt with these changes.

## Local Keycloak and platform console verification (2026-11-17)

- Backend Ruff check, Ruff format check and MyPy: passed.
- Full backend suite with PostgreSQL integration enabled: 15 passed. Warnings: Starlette/httpx deprecation and a local pytest cache write warning; neither changed test results.
- Console strict `tsc --noEmit`: passed with TypeScript 6.0.3.
- Next.js 16.4.6 optimized production build: passed; static `/` generated.
- Real Keycloak Authorization Code + PKCE S256 login: passed without displaying credentials, authorization code or tokens.
- Access token issuer, `control-api` audience and `platform-operator` realm role checks: passed.
- Authorized `GET /api/v1/tenants`: passed. Unauthenticated request returned 401.
- CORS preflight allowed `http://localhost:3000` and the Authorization header.
- Recreated API reports healthy/ready; recreated console returns HTTP 200 on loopback port 3000.
- No browser automation tool was available for a visual click-through; manual sign-in/UI interaction remains for the user. No vulnerability scan, accessibility audit, MFA/session-revocation test or production identity review was performed.

## Deletion request and console redesign (2026-11-17)

- Migration `004_tenant_deletion_request` applied through `platform_control_migrator`; Alembic reports it as head.
- Privilege verification returned `f|t|t|f`: no table-wide runtime UPDATE, UPDATE permitted on `status` and `updated_at`, denied on `display_name`.
- Ruff check, Ruff formatting and MyPy: passed.
- Full suite with PostgreSQL integration: 15 passed; the existing Starlette/httpx and local pytest-cache warnings remain.
- Strict TypeScript check and Next.js 16.4.6 production build: passed.
- Updated API and console images built and recreated; API healthy, console HTTP 200, DELETE present in OpenAPI.
- No real tenant was modified during container smoke checks. Visual browser automation was unavailable, so final appearance and interaction require the user's manual browser review.
- DELETE CORS regression: the initial browser attempt was blocked because only GET/POST were allowlisted. DELETE was added explicitly; the full suite now passes 16 tests and the running preflight returns 200 with `GET, POST, DELETE`.

## Local domain verification and first onboarding (2026-11-17)

- Migration `005_tenant_domains` applied through `platform_control_migrator`; Alembic reports it as head.
- Ruff, formatting and MyPy passed; full PostgreSQL suite passed 19 tests with the existing two warnings.
- Tests cover hostname normalization, public-host rejection, duplicate ownership, unconfigured verification failure, successful verification, listing and database-backed preview resolution.
- Real Keycloak-protected onboarding created Lifemac Pharma in `PENDING` and verified `lifemac.localhost` with method `LOCAL`.
- Running preview resolved `lifemac.localhost` to the correct opaque tenant ID with `VERIFIED` domain status; `unknown.localhost` returned 404.
- No public DNS, hosting provider, tenant service database or activation was performed.

## Provisioning orchestration boundary (2026-11-17)

- Migration `006_provisioning_jobs` was applied through the dedicated `platform_control_migrator` service; Alembic reports it as head.
- Ruff check/format and strict MyPy passed. Full unit, security and PostgreSQL integration suite: 24 passed, with the existing Starlette/httpx deprecation warning.
- The API supports idempotent fixture provisioning requests, job listing, failed-job retry and service-database metadata listing. Unknown services are rejected by both request validation and database constraints.
- The isolated worker uses `platform_control_worker` for job metadata and `tenant_database_provisioner` only for PostgreSQL infrastructure. Neither credential exists in `RuntimeSettings` or the API container configuration.
- Lifemac Catalogue and Inventory fixture jobs reached `INFRASTRUCTURE_READY`. Both runtime roles authenticated to their own opaque databases; Catalogue-to-Inventory connection was denied.
- Both databases are owned by their service migrator roles. Runtime/migrator roles are LOGIN roles with no superuser, CREATEDB or CREATEROLE capability and connection limit 20. PUBLIC has neither CONNECT nor TEMPORARY.
- Generated passwords were not printed or stored in control-plane metadata. Only local secret-volume references were persisted.
- The first Catalogue attempt failed because PostgreSQL rejected a bind placeholder in `CREATE ROLE ... PASSWORD`; no roles/database were created. The safe SQL-literal composition fix was applied and the durable retry completed on attempt 2.
- Tenant remains `PROVISIONING`; no service migration was executed and the tenant was not marked ACTIVE. Two-tenant isolation and the Phase 1B human exit gate remain outstanding.

## Tenant database/schema architecture revision (2026-11-17)

- Updated the repository rule and ADR-015: new provisioning uses one opaque database per tenant and one schema per enabled service.
- Migration `007_tenant_database_schemas` was applied by `platform_control_migrator`; `tenant_databases` exists and service metadata now supports `tenant_database_id` and `schema_name`.
- Updated worker identity derivation, schema creation and schema USAGE permissions. Static checks passed: Ruff and strict MyPy.
- Existing Catalogue/Inventory per-service databases and old metadata are intentionally preserved. No destructive cleanup or data migration has been performed.
- The new worker path still requires a focused runtime smoke test before retiring the legacy fixture databases.
- Focused runtime smoke test subsequently passed: Lifemac Catalogue and Inventory both reached `INFRASTRUCTURE_READY` in the same tenant database (`t_49e84243...`) with distinct `catfx` and `invfx` schemas. Migration `008_shared_db` removed the obsolete global `database_name` uniqueness constraint. The worker role-set failure was fixed by granting temporary role SET/ADMIN options during provisioning; those grants are revoked by the worker after setup.
- Migrations `009_service_ready` and `010_active_status` were applied. Lifemac remains `PROVISIONING`; service readiness rows are `PENDING` until owning-service migrations and smoke checks run. The activation endpoint rejects incomplete tenants instead of allowing premature `ACTIVE` state.

## 2026-11-17 control-plane continuation

- The dedicated owning-service migration runner was rebuilt and executed through the `service-migration` Compose profile using each service's migrator credential. Both Lifemac readiness rows are now `MIGRATED`/`PASSED`.
- Verified tenant database tables: `catfx.products` and `invfx.stock_items` in `t_49e84243f9e44981b3a538f943cc79ba`.
- Migrator roles have `USAGE, CREATE` only on their service schemas; runtime roles retain schema `USAGE` and table DML grants. The control-plane worker does not execute owning-service DDL.
- `docker compose --env-file .env -f .\\infra\\local\\compose.yaml config --quiet` passed. PostgreSQL, Redis, Mailpit, Keycloak, API, worker, and console containers were running; API `/health` returned `ok`; all published ports remained loopback-bound.
- Backend scoped Ruff (excluding repository executable-bit/shebang noise) and strict MyPy passed in the built image.
- Lifemac is intentionally still `PROVISIONING` until the authenticated activation endpoint is exercised; no premature activation was performed. A second-tenant isolation proof and the final human exit-gate walkthrough remain outstanding.
- Follow-up verification: Lifemac is now `ACTIVE`, with a `TENANT_ACTIVATED` audit event. The authenticated activation flow completed successfully after both service readiness rows were `MIGRATED`/`PASSED`.
