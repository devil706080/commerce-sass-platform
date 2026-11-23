# Identity & Access

**Status:** Tenant staff identity boundary implemented; live local database verification remains
environment-dependent.

## Implemented scope

This service owns tenant-scoped staff principals, invitations and memberships. Keycloak performs
local OIDC authentication; this service remains the source of truth for tenant membership and
staff role authorization. A Keycloak realm role alone does not grant access to tenant data.

Implemented endpoints:

- `POST /api/v1/staff/invitations` creates an idempotent seven-day invitation.
- `POST /api/v1/staff/invitations/accept` binds the verified OIDC issuer/subject to the invited
  email and activates the tenant membership.
- `GET /api/v1/me` returns the caller's active membership.
- `GET /api/v1/staff` lists tenant staff for an owner or administrator.
- `GET /health` reports process liveness without exposing tenant or credential information.

Roles are `TENANT_OWNER`, `TENANT_ADMIN`, `CATALOGUE_MANAGER`, `ORDER_MANAGER` and `VIEWER`.
Platform operators may only create the first owner invitation. After owner bootstrap, tenant
owners/admins manage staff; only an owner may invite another owner.

## Security and tenant boundary

- Requests fail closed unless the normalized hostname is in `IDENTITY_ALLOWED_HOSTS`.
- The browser cannot select a tenant using a header, query parameter or request body.
- Bearer tokens must be RS256 tokens with the configured issuer, `identity-api` audience,
  expiration, subject, email and `email_verified=true`.
- Principal identity is `(issuer, subject)`; matching email alone never links accounts.
- The runtime role has table DML only. The independent migrator role owns schema changes.
- Database passwords are read from a mounted tenant-specific secret file and never embedded in
  the image or committed Compose configuration.
- The Identity volume contains only the selected service secret. The shared provisioner secret
  volume must not be mounted into this runtime.

## Local configuration

The Control Plane must first provision `identity_access` for the tenant. Configure these ignored
local environment values from the provisioning metadata (none are passwords):

```text
IDENTITY_TENANT_ID
IDENTITY_ALLOWED_HOSTS
IDENTITY_DATABASE_NAME
IDENTITY_RUNTIME_ROLE
IDENTITY_MIGRATOR_ROLE
IDENTITY_CORS_ORIGINS
```

The selected provisioned credential JSON must be copied, without printing it, into the dedicated
`identity_secrets` volume as `/database.json`, owned by container UID/GID `10004` with mode `0600`.
Then run the owning-service migration before starting the API:

```powershell
docker compose --env-file .env -f .\infra\local\compose.yaml --profile identity-migration run --rm identity-access-migrate
docker compose --env-file .env -f .\infra\local\compose.yaml --profile identity --profile identity-access up -d --build keycloak identity-access
```

Do not use the PostgreSQL bootstrap administrator, provisioner or Control Plane credentials for
this service.

## Development checks

From this directory:

```powershell
uv sync --locked --group dev
uv run --group dev ruff check src tests
uv run --group dev mypy src
uv run --group dev pytest -q
```

## Deliberately pending

This increment does not implement customer password/OTP/social login, server-managed browser
sessions, MFA, recovery, session revocation, invitation email delivery, staff role/status mutation
or audit-event publication. Those require separately approved Identity increments and provider
decisions. The Tenant Admin UI integration is a separate application task and must consume these
APIs; it must not write Identity tables directly.
