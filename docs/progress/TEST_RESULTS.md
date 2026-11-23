# Test results

## Central tenant branding and curated themes (2026-11-18)

- Alembic revisions `012_tenant_branding` and `013_branding_privileges` were applied by the dedicated Control Plane migrator; `013_branding_privileges` is the verified head.
- The existing Lifemac tenant was backfilled as `Lifemac Pharma`, initials `LP`, theme `ocean_teal`; the table contains one branding row.
- Scoped Ruff lint and formatting checks passed. Strict MyPy passed for all 25 Control Plane source files.
- Control Plane unit and security suites passed: 25 tests. A pre-existing Starlette/httpx deprecation warning remains.
- A focused PostgreSQL integration test passed the transactional create/read/update flow and verified all five theme definitions and the Berry palette response.
- Platform Console TypeScript checking and the optimized Next.js production build passed.
- Compose configuration validation and image builds passed. Recreated Control Plane and Console containers are running; API and console returned HTTP 200.
- OpenAPI exposes both theme/branding paths. Unauthenticated theme access returned 401.
- Runtime privilege result was `(False, True, False, False, True)`: no table-wide UPDATE, theme-key UPDATE allowed, logo UPDATE denied, no table-wide INSERT, required tenant-id INSERT allowed.
- An authenticated manual browser walkthrough of theme selection remains for the operator. Tenant Admin/Storefront theme consumption and logo upload were deliberately not included in this Control Plane-only slice.

## Identity & Access provisioning boundary (2026-11-18)

- Migration `014_identity_access` was applied through `platform_control_migrator`; Alembic reports it as head.
- Ruff lint and scoped formatting passed. Strict MyPy passed across all 25 Control Plane source files.
- Unit and security regression suites passed: 27 tests, with the existing Starlette/httpx deprecation warning.
- A focused PostgreSQL integration test passed: an active tenant requested `identity_access`, received a pending job, and remained `ACTIVE`.
- Tests verify deterministic `identity` schema/role names, shared opaque tenant-database placement, unknown-service rejection and exclusion from the legacy cross-service migration helper.
- The real Lifemac `identity_access` infrastructure job reached `INFRASTRUCTURE_READY` after the
  provisioner was corrected to avoid granting an ADMIN option back to its own grantor. No password
  was displayed. The owning-service migration has not yet been verified against the dedicated
  Identity secret volume.
- Identity & Access Ruff passed, strict MyPy passed for 17 source files, and 8 unit/security tests
  passed. Tests cover email normalization, first-owner bootstrap restrictions, missing/suspended
  membership denial, invitation acceptance denial, normalized host allowlisting and OpenAPI Bearer
  security documentation. One upstream Starlette/httpx deprecation warning remains.
- Control Plane compatibility Ruff and strict MyPy passed; 27 unit/security tests passed with the
  same upstream warning after supplying test-only environment values.
- Keycloak realm JSON and Compose YAML syntax were validated. Docker image/container, PostgreSQL
  migration/privilege and real browser login tests were not rerun because Docker CLI was not
  available to the Codex process. They remain required before the UI integration gate.

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

## Initial tenant-owner contact (2026-11-19)

- Added migration `015_owner_contact`; the full Alembic chain rendered successfully offline.
- Ruff check passed, Ruff format check passed, and strict MyPy passed for 25 source files.
- 32 Control Plane unit/security tests passed. New tests cover standards-based email validation,
  whitespace/case normalization and invalid email denial. One upstream Starlette/httpx deprecation
  warning remains.
- Migration `015_owner_contact` was applied with the dedicated migrator and is the verified head.
  The column is nullable for existing-data safety. Runtime has no table-wide INSERT, but has scoped
  INSERT and UPDATE on `initial_owner_email`; one existing tenant currently lacks a contact.
- The complete Control Plane suite passed against local PostgreSQL: 37 tests. Integration writes
  ran in rolled-back transactions. The existing Starlette/httpx deprecation warning remains.
- Platform Console strict TypeScript checking and the optimized Next.js 16.4.6 production build
  passed inside Docker; static `/` generation completed.
- Control Plane and Platform Console images rebuilt and containers were recreated. API health and
  readiness returned `ok`; console returned HTTP 200; both published ports are loopback-only.
- OpenAPI exposes the owner-contact endpoint and requires `initial_owner_email` for tenant creation.
  Unauthenticated tenant access returned 401, and the authenticated-origin PUT CORS preflight
  returned 200 with `GET, POST, PUT, DELETE`.
- In-app browser automation was unavailable, so the final Keycloak login/modal walkthrough remains
  a manual operator check. No project-owned dangling image remained after the rebuild.

## Platform Console local-domain workflow (2026-11-19)

- Added an operator UI for selecting a tenant, registering a `localhost` hostname, listing its
  persisted domain records and invoking the existing deterministic local verification endpoint.
- Domain verification remains fail-closed: a hostname absent from `LOCAL_TENANT_LABELS` returns the
  backend error and is not shown as verified. Domain writes remain restricted to pending tenants.
- Direct strict TypeScript checking passed. The Docker production build then passed its own
  TypeScript check, Next.js optimized compilation and static page generation.
- The Platform Console image was rebuilt and its container recreated. Console HTTP returned 200;
  Control Plane health/readiness returned `ok`; ports 3000 and 8000 remained loopback-only.
- Authenticated visual interaction still requires the operator's manual Keycloak session because an
  in-app browser automation facility was unavailable in this execution environment.

## Tenant application-domain contract (2026-11-19)

- Migration `016_domain_purpose` was rendered offline, preflighted against existing rows, applied
  with the dedicated migrator and verified as the database head. Existing
  `lifemac.localhost` remains `STOREFRONT` and `VERIFIED`.
- Domain records now distinguish Storefront from Tenant Admin. Hostnames remain globally unique,
  and each tenant may own at most one hostname for each purpose.
- Local `*.localhost` verification is database-backed and no longer requires
  `LOCAL_TENANT_LABELS`. Active tenants can add a missing Tenant Admin hostname; tenants awaiting
  deletion cannot change domains.
- Ruff (excluding the repository's known Windows executable-bit noise), Ruff formatting, strict
  MyPy, offline Alembic rendering and the full PostgreSQL suite passed. Test result: 37 passed with
  one upstream Starlette/httpx deprecation warning.
- The Control Plane image was rebuilt and recreated. Health/readiness returned `ok`; OpenAPI
  includes the domain purpose contract; unauthenticated domain access returned 401.
