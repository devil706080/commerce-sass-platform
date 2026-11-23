# Implementation tracker

Platform Control Plane, Phase 1B: **implemented and locally verified**. The Lifemac tenant has passed Catalogue and Inventory migration/smoke readiness and was activated through the authenticated console flow. The local control-plane exit gate is complete; production hardening and additional tenants remain outside this phase.

## Initial tenant-owner contact (2026-11-19)

- New tenant creation now requires a validated, normalized initial owner email as onboarding
  metadata. The value participates in idempotency hashing and is returned only through the
  operator-authenticated Control Plane API.
- Existing tenants may receive or correct this value through an audited owner-contact endpoint.
  Audit records contain the operator issuer/subject and action but not the email address.
- Migration `015_owner_contact` adds the nullable column for existing-data safety and restricts
  runtime INSERT/UPDATE to required tenant columns. It is applied and verified as the Alembic head.
- The Platform Console now requires this email during onboarding, displays missing/existing owner
  contacts, and provides an audited editor for existing tenants such as Lifemac.
- Identity & Access is selected by default alongside Catalogue, Inventory and Media during tenant
  provisioning, and its job is labelled correctly in the provisioning dashboard.
- The Control Plane does not create Keycloak users or Identity memberships. The next approval gate
  is Tenant Admin invitation acceptance and membership enforcement.
- The Platform Console now exposes the existing local-domain workflow instead of leaving Domains
  disabled: operators can select a tenant, register a unique `*.localhost` hostname, review its
  persisted status and request deterministic local verification.
- Verification still requires the hostname in `LOCAL_TENANT_LABELS`, and the backend—not the UI—is
  authoritative. Provisioning remains a separate action after owner contact and domain verification.

## Central tenant branding and curated themes (2026-11-18)

- The Control Plane now owns one branding record per tenant, including customer-facing display name, fallback initials, a stable theme key, and a reserved nullable Media logo reference.
- Operators can select one of five curated light themes: Ocean Teal, Emerald, Indigo, Berry, or Amber. There is intentionally no dark/light mode toggle and arbitrary operator-supplied colors are not accepted.
- Tenant creation persists the registry record and its initial branding in the same database transaction. Existing tenants were backfilled; Lifemac Pharma is stored as `LP` with `ocean_teal`.
- Authenticated Control Plane endpoints list the curated themes and read/update a tenant's branding. Updates generate an operator-attributed audit event.
- The Platform Console provides visual theme cards during onboarding and when editing an existing tenant's branding.
- Runtime database writes are column-scoped. The runtime role cannot perform table-wide INSERT/UPDATE and cannot update the reserved `logo_media_id` column.
- This slice does not yet make Tenant Admin or Storefront consume the selected theme. Dynamic frontend application and logo upload remain the next explicitly separate implementation step.

## Identity & Access provisioning boundary (2026-11-18)

- The Control Plane now accepts `identity_access` as a provisionable tenant service and derives an opaque, tenant-scoped `identity` schema with dedicated runtime and migrator roles.
- New tenants can include Identity & Access in their initial provisioning workflow. Existing `ACTIVE` tenants can enable it without being moved backward to `PROVISIONING`.
- The legacy Control Plane service-migration helper is explicitly restricted to its existing Catalogue/Inventory fixtures. It cannot create Identity or Media tables; each owning service must run its own migrations.
- Migration `014_identity_access` is applied. This increment intentionally does not create Keycloak users, invitations or memberships in the Control Plane database.
- The independent Identity & Access service now owns its `identity` migration, verified OIDC
  subject binding, first-owner bootstrap, staff invitations and tenant memberships. Tenant roles
  are enforced from the Identity database rather than trusting a Keycloak realm role alone.
- The service has dedicated runtime/migrator configuration, a tenant-host fail-closed boundary,
  an `identity-api` Keycloak audience and an isolated read-only Identity secret volume.
- Local live migration/API verification remains open because Docker CLI was unavailable to the
  current Codex execution environment. The next approval gate is the separate Tenant Admin UI
  integration after that runtime check passes.

## Increment B: first registry slice in progress

Duplicate-name protection is deployed. The owner-approved migration `002_unique_tenant_name` added a unique index over `lower(btrim(display_name))`. Names differing only by case or outer whitespace are rejected even if they belong to different real businesses; a future approved business-identity policy may be needed. Existing collisions make the migration fail without deleting data.

An environment-configured local browser label preview is deployed and tested. It is not a trusted domain resolver, an authentication mechanism, or a tenant database router.

- API: `POST /api/v1/tenants` creates a pending tenant; GET retrieves/lists with bounded pagination; DELETE requests audited offboarding by transitioning to `DELETION_REQUESTED`. Operator access requires a validated Keycloak token and role; caller-provided tenant/operator headers remain untrusted.
- Owner-approved migrations `001_tenant_registry` through `005_tenant_domains` are applied. Audit events record the authenticated OIDC issuer/subject; no password or token is persisted. Runtime updates remain column-scoped.
- The approved migration was run as `platform_control_migrator`. Runtime gets only the table privileges needed for implemented operations. Worker, provisioner and bootstrap credentials stay out of the HTTP process. No future database permission, role, or schema changes are authorized by this document alone.
- Domain verification, lifecycle transitions, additional configuration and provisioning remain later work; no unauthenticated public tenant operations or placeholder allow-all authentication are acceptable.

## Platform console and operator access: local slice implemented

- A separate Next.js console runs at localhost:3000 and calls only the Control Plane API.
- Local Keycloak provides realm `platform-local`, public client `platform-console`, PKCE S256 and the `platform-operator` role. Direct password grants are disabled.
- The API independently verifies signature, issuer, audience, expiry, subject and role through Keycloak JWKS. UI state or caller headers cannot bypass it.
- Identity secrets are generated into ignored `.env`; the UI does not store them and access tokens remain in Keycloak JS memory.
- The redesigned console includes registry metrics, search/status filters, responsive rows, creation and protected deletion-request dialogs, loading/empty/error/success states, ID copy and explicit future-feature boundaries.
- Tenant lifecycle and operator identity may need new database tables or grants. Each migration must be presented for explicit owner approval before it runs, and executed with the relevant migrator role. Do not use the bootstrap administrator in an application.
- A tenant's browser hostname or local preview label is not proof of identity, authorization, domain verification, or readiness for activation.
- Owner authorized applying necessary schema changes without asking each time until that instruction is changed. Migrations through `005_tenant_domains` were applied using the migrator; future migrations still require review, clear reporting, and least-privilege execution.

## First local tenant onboarding

- `Lifemac Pharma` exists as an opaque tenant record in `PENDING` state.
- `lifemac.localhost` is registered and `VERIFIED` using the deterministic local adapter.
- Local preview resolution requires both `.env` allowlisting and the verified database mapping; unknown hosts return 404.
- Verification does not activate the tenant. Provisioning and activation gates remain next work.

### Remaining identity work

The local provider is not the production identity decision. Production still needs MFA, separate super-admin/support permissions, session revocation and step-up policy, rate limiting, HTTPS/secure cookies or a reviewed BFF session design, monitoring and provider selection. The current broad `platform-operator` role is sufficient only for this local slice. Domain/lifecycle/provisioning work remains incomplete, so the Phase 1B exit gate has not passed.
