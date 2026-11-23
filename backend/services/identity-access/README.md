# Identity & Access

**Status:** Dynamic tenant staff identity boundary implemented. Container/runtime verification is
required after rebuilding the local stack.

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

- The Tenant Admin server sends a short-lived Control Plane-signed context created from a verified,
  active Tenant Admin hostname. Identity validates its issuer, audience, signature and expiry.
- The browser cannot select a tenant, database, role or secret reference using a header, query
  parameter or request body.
- Bearer tokens must be RS256 tokens with the configured issuer, `identity-api` audience,
  expiration, subject, email and `email_verified=true`.
- Principal identity is `(issuer, subject)`; matching email alone never links accounts.
- The runtime role has table DML only. The independent migrator role owns schema changes.
- Database passwords are resolved from the signed secret reference in the local read-only secret
  volume and never enter a token, browser response, image or committed Compose configuration.
- The exact verified initial-owner email may claim the first owner membership once. After that,
  access always requires the tenant database membership bound to `(issuer, subject)`.

## Local configuration

The Control Plane must provision and migrate `identity_access` for each tenant. Runtime tenant
routing is automatic; configure only shared infrastructure/OIDC settings and generated secrets:

```text
TENANT_CONTEXT_BROKER_TOKEN
TENANT_CONTEXT_SIGNING_SECRET
IDENTITY_OIDC_ISSUER
IDENTITY_OIDC_AUDIENCE
IDENTITY_OIDC_JWKS_URL
```

The local Keycloak synchronizer reads active verified admin hostnames from the protected Control
Plane endpoint and registers exact redirect origins; it also removes the obsolete hardcoded
`tenant_id` mapper. No tenant hostname or ID is committed to the realm configuration.

```powershell
docker compose --env-file .env -f .\infra\local\compose.yaml --profile identity --profile platform-control --profile identity-access up -d --build keycloak platform-control identity-access identity-config-sync
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
decisions. Tenant Admin consumes these APIs only through its server gateway and never writes
Identity tables directly.
