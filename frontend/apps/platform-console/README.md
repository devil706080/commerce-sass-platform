# Platform administration console

The local operator console uses Keycloak Authorization Code + PKCE S256. A signed token must contain the `platform-operator` realm role and the `control-api` audience. The current UI lists registered tenants and creates tenants in `PENDING` status.

The browser never connects to PostgreSQL. It calls the Platform Control Plane API, and the API uses its least-privilege runtime database role.

From the repository root, generate missing local identity values once and start the selected profiles:

```powershell
python .\scripts\bootstrap_identity.py
docker compose --env-file .env -f .\infra\local\compose.yaml --profile identity --profile platform-control --profile platform-console up -d --build
```

Open `http://localhost:3000`. The generated operator email and password are stored only in the ignored `.env`; do not commit or display them.

Keycloak runs in development mode for localhost only. MFA, granular admin/support roles, production TLS, server-managed browser sessions, rate limiting and production identity-provider configuration remain required before production use.
