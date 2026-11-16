# AGENTS.md — Commerce SaaS Platform Engineering Rules

## Mission
Build a generic, white-label, multi-tenant commerce SaaS product. Lifemac Pharma is the first example tenant only. The platform must onboard other businesses through configuration, not code forks.

## Mandatory reading
Before any task, read: `README.md`, `docs/product/PRD.md`, the relevant section of `docs/architecture/PHASE_0_1_DELIVERY_BLUEPRINT.md`, the relevant service README, accepted ADRs and API/event contracts.

## Repository boundaries
- `frontend/` contains only frontend apps and frontend-only shared packages.
- `backend/` contains independently structured backend services, backend contracts and backend tests.
- `infra/` contains local infrastructure and future deployment definitions.
- Each backend service owns its dependency manifest and lockfile, configuration, Dockerfile, database/migrations, domain model, repositories, tests and release boundary.
- No cross-service ORM/domain/repository imports and no cross-database SQL joins.
- Shared libraries are small, technical, versioned and intentionally limited; do not create a shared business-domain package.

## Non-negotiable architecture rules
1. Multi-tenant SaaS, not a one-tenant Lifemac application.
2. Tenant commerce data uses database-per-tenant-per-service. Provision only enabled tenant/service database pairs.
3. The singleton platform-control database stores platform metadata only: tenant registry, verified domains, lifecycle, plans/entitlements and database/secret references. It is not a commerce database.
4. The Control Plane provisions databases, roles and secret references through a separate privileged worker. Each service runs its own migrations using its own migrator identity. The Control Plane must not apply another service's migrations.
5. Revoke PostgreSQL `CONNECT` and `TEMPORARY` from `PUBLIC` on every tenant/service database. Grant database access only to that service's runtime/migrator roles. Runtime roles are not owners, superusers, `CREATEDB` or `CREATEROLE`.
6. Use opaque generated tenant IDs in resource names; never use a business display name or unsanitized slug as a SQL identifier.
7. Tenant routing comes from trusted ingress and verified domain mapping. Never trust a browser-supplied tenant ID/header/query/body as authorization or database-routing authority. Validate signed internal tenant context (issuer, audience, expiry, key ID/signature) and tenant lifecycle state.
8. Resolve tenant membership/role separately from tenant identification. Authorize every object operation. Platform operator identity is separate from tenant staff and customer identity.
9. Never read or write another service's database. Communicate through versioned APIs or versioned events. Use transactional outbox and idempotent consumers for reliable domain events.
10. Redis is cache/ephemeral state only, never the source of truth for orders, payment, price or inventory. Define TTL, invalidation, tenant-aware keys and outage behavior.
11. Kafka is a deferred event-streaming option, not a generic background queue. RabbitMQ is optional for queued jobs when a real consumer/retry requirement exists.
12. Do not create cloud resources, Azure resources, EC2 instances, public DNS or production ingress in Phase 1A/1B. Do not implement AI before its phase.

## Payment security rules
- No application API, frontend state or backend model may receive/store raw PAN, CVV/CVC, PIN/PIN block or track data.
- Use PSP-hosted checkout/hosted fields/tokenization so card entry goes directly to the PSP.
- Store only provider references and approved display metadata such as card brand/last four where required. CVV is never retained, even encrypted or masked.
- Masking is UI presentation only; it does not make raw card data safe to store.
- Verify provider webhook signatures, enforce idempotency/replay protection, reconcile provider state server-to-server and never trust browser redirect as payment confirmation.
- Tenant PSP credentials are isolated and encrypted. Tenant customer payments and platform SaaS subscription billing are separate bounded contexts.

## Security and quality rules
- Deny by default; least privilege everywhere.
- Passwords use Argon2id or a reviewed equivalent; OTPs are hashed, short-lived, single-use and rate-limited.
- OAuth/OIDC Authorization Code + PKCE S256; exact redirect allowlists; validate state/nonce; secure cookies; CSRF protections for cookie-authenticated writes.
- Enforce request size limits, pagination, input validation, output encoding, CSP/security headers, upload content checks and safe non-executable media storage.
- Keep PII, tokens, OTPs, PAN/CVV and secrets out of logs, events, traces and analytics.
- Test cross-tenant denial, service/database credential boundaries, authentication, authorization, abuse, idempotency, retries, failure recovery and migrations.
- Never claim zero vulnerabilities or compliance certification. Report actual test/scanner results, residual risks and external validation required.

## Service-by-service workflow
1. Identify the approved phase and exactly one service/app.
2. Read its README, PRD scope, relevant ADRs and upstream/downstream contracts.
3. Before editing, present plan, files, boundaries, data ownership, security risks and tests.
4. Confirm API/event and database contracts before behavior implementation.
5. Implement only that service/app. Do not scaffold other services as a side effect.
6. Run formatter, lint, type checks, unit, integration, contract, tenant-isolation and security tests as applicable. Report exact commands and true results.
7. Run the service in isolation first; integrate one dependency at a time.
8. Update docs, ADRs and contracts when decisions change.
9. Explain code paths, data flow, security controls and trade-offs in plain language.
10. Stop at the human approval gate. Never proceed to the next service automatically.

## Frontend rules
- Keep `storefront`, `tenant-admin` and `platform-console` independent apps.
- Frontends call APIs; they never connect to databases or authoritatively calculate price, tax, stock, payment or order state.
- Shared UI is brand-neutral. Brand tokens/content come from validated tenant configuration.
- Responsive UX, accessibility, loading/empty/error states, visual quality and E2E coverage are acceptance criteria.

## Required completion report
State task/phase, single service/app changed, files changed, data/migration/API/event effects, security and tenant isolation, exact tests and results, limitations, known risks, plain-language implementation explanation and one recommended next task. Do not execute the next task without approval.
