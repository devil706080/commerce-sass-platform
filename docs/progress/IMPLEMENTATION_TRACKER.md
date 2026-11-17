# Implementation tracker

Platform Control Plane, Phase 1B: **foundation, first tenant-registry slice, local Keycloak authentication and operator console implemented; human review pending**. The images build and the local containers are healthy. Schema changes were applied with the migrator role. Domain verification, lifecycle transitions and provisioning are not implemented. See TEST_RESULTS.md.

## Increment B: first registry slice in progress

Duplicate-name protection is deployed. The owner-approved migration `002_unique_tenant_name` added a unique index over `lower(btrim(display_name))`. Names differing only by case or outer whitespace are rejected even if they belong to different real businesses; a future approved business-identity policy may be needed. Existing collisions make the migration fail without deleting data.

An environment-configured local browser label preview is deployed and tested. It is not a trusted domain resolver, an authentication mechanism, or a tenant database router.

- API: `POST /api/v1/tenants` creates a pending tenant with a server-generated UUID; `GET /api/v1/tenants/{tenant_id}` retrieves it; `GET /api/v1/tenants` lists it with bounded pagination. Operator access now requires a validated Keycloak token and role; caller-provided tenant/operator headers remain untrusted.
- Owner-approved migrations `001_tenant_registry`, `002_unique_tenant_name` and `003_audit_actor` are applied. Audit events record the authenticated OIDC issuer/subject; no password or token is persisted.
- The approved migration was run as `platform_control_migrator`. Runtime gets only the table privileges needed for implemented operations. Worker, provisioner and bootstrap credentials stay out of the HTTP process. No future database permission, role, or schema changes are authorized by this document alone.
- Domain verification, lifecycle transitions, additional configuration and provisioning remain later work; no unauthenticated public tenant operations or placeholder allow-all authentication are acceptable.

## Platform console and operator access: local slice implemented

- A separate Next.js console runs at localhost:3000 and calls only the Control Plane API.
- Local Keycloak provides realm `platform-local`, public client `platform-console`, PKCE S256 and the `platform-operator` role. Direct password grants are disabled.
- The API independently verifies signature, issuer, audience, expiry, subject and role through Keycloak JWKS. UI state or caller headers cannot bypass it.
- Identity secrets are generated into ignored `.env`; the UI does not store them and access tokens remain in Keycloak JS memory.
- Tenant lifecycle and operator identity may need new database tables or grants. Each migration must be presented for explicit owner approval before it runs, and executed with the relevant migrator role. Do not use the bootstrap administrator in an application.
- A tenant's browser hostname or local preview label is not proof of identity, authorization, domain verification, or readiness for activation.
- Owner authorized applying necessary schema changes without asking each time until that instruction is changed. Migration `003_audit_actor` was applied using the migrator; future migrations still require review, clear reporting, and least-privilege execution.

### Remaining identity work

The local provider is not the production identity decision. Production still needs MFA, separate super-admin/support permissions, session revocation and step-up policy, rate limiting, HTTPS/secure cookies or a reviewed BFF session design, monitoring and provider selection. The current broad `platform-operator` role is sufficient only for this local slice. Domain/lifecycle/provisioning work remains incomplete, so the Phase 1B exit gate has not passed.
