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
