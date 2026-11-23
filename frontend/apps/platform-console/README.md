# Platform administration console

The local operator console uses Keycloak Authorization Code + PKCE S256. A signed token must contain the `platform-operator` realm role and the `control-api` audience. The dashboard lists and searches tenants, creates tenants in `PENDING` status with an initial administrator contact, edits that contact for existing tenants, selects branding, registers and verifies local tenant domains, starts service provisioning and submits confirmed, audited deletion requests.

The browser never connects to PostgreSQL. It calls the Platform Control Plane API, and the API uses its least-privilege runtime database role.

From the repository root, generate missing local identity values once and start the selected profiles:

```powershell
python .\scripts\bootstrap_identity.py
docker compose --env-file .env -f .\infra\local\compose.yaml --profile identity --profile platform-control --profile platform-console up -d --build
```

Open `http://localhost:3000`. The generated operator email and password are stored only in the ignored `.env`; do not commit or display them.

Deletion is deliberately a lifecycle request, not a hard-delete. The UI requires the operator to type the tenant name, and the API changes status to `DELETION_REQUESTED`. Retention review and final offboarding remain future workflow steps.

The initial administrator email is not a password and does not create a Keycloak account. For
local testing, create a verified Keycloak user with the exact same email. Identity & Access is
selected by default during tenant provisioning; the separate Tenant Admin application will bind
the verified Keycloak subject to the pending owner membership.

Keycloak runs in development mode for localhost only. MFA, granular admin/support roles, production TLS, server-managed browser sessions, rate limiting and production identity-provider configuration remain required before production use.
