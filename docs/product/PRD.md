# Table of Contents

# Commerce SaaS Platform

## Product Requirements Document and Architecture Blueprint

**Document status:** Product requirements baseline; technical
architecture baseline completed, pending human approval  
**Version:** 1.0  
**Prepared:** 16 November 2026  
**Product type:** Generic multi-tenant, white-label commerce SaaS
platform  
**First tenant:** Lifemac Pharma  
**Delivery approach:** Phased, monorepo, independently deployable
microservices  
**Initial runtime:** Local development using Docker Compose; hosting is
deliberately deferred

## 0. Executive direction

This repository defines a reusable, white-label, multi-tenant e-commerce
SaaS platform. Lifemac Pharma is the first example tenant/customer, not
the product name or repository name. The product is not a Lifemac-only
store and is not initially a multi-vendor marketplace. A future client
should be onboarded through the platform control plane and receive an
independently branded storefront, tenant administration area, domain
configuration, product catalogue, customers, orders, inventory, payment
configuration, policies and business settings without creating a
separate codebase.

The platform must be designed around two isolation requirements at the
same time:

1.  **Database-per-tenant:** tenant business data must not be placed in
    shared tenant tables. Each tenant receives dedicated database
    boundaries. There is no shared products table containing every
    tenant's products.

2.  **Database-per-service:** every microservice owns its data and
    database lifecycle. A service must not read or write another
    service's database directly.

The resulting target is **database-per-tenant-per-service** for tenant
business data. For example, each tenant has a catalogue database owned
by the Catalogue service, an inventory database owned by the Inventory
service, an orders database owned by the Orders service, and so on. A
separate, small **platform control-plane database** stores SaaS metadata
only: tenant registry, verified domain-to-tenant mappings, tenant
lifecycle state, plan/entitlement metadata and provisioning references.
It must not become a shared store for tenant products, carts, customer
profiles, payment methods or orders.

The platform will use a monorepo while keeping services independently
structured, testable, built, versioned and deployable. Services
communicate through versioned APIs and asynchronous domain events.
Cross-service database joins and shared ORM models are prohibited.

For card payments, the platform will not collect or store raw card
numbers or CVV/CVC. Card entry must be handled by a PCI-compliant
payment provider using hosted checkout or provider-hosted
fields/tokenization. The platform stores only the provider's references
and limited display metadata, such as card brand and last four digits,
where returned and permitted. CVV must never be stored, including
encrypted or masked. The UI can display a masked representation such as
Visa •••• 4242; masking is a display control, not permission to store
the complete card number.

The first goal is a complete and reliable commerce platform. AI
integration follows the core commerce phases. Production hosting, public
exposure and deployment architecture are later phases. No Azure or other
cloud service is a dependency for the initial build.

**Document precedence:**
docs/architecture/PHASE_0_ARCHITECTURE_BASELINE.md is the controlling
technical baseline; PHASE_1_LOCAL_FOUNDATION.md controls local setup. If
older PRD wording conflicts with those documents or accepted ADRs, stop
and raise the conflict rather than improvising.

**Security statement:** No architecture can honestly promise zero
vulnerabilities. This blueprint defines security controls, verification
gates and operational practices to reduce risk and detect weaknesses. A
production release still requires independent security review,
payment-provider/acquirer confirmation and applicable compliance
assessment.

## 1. Product vision and goals

### 1.1 Vision

Provide a premium, configurable commerce platform that allows a business
to launch and operate its own online store with a distinctive brand,
without needing a bespoke software build. The customer experience should
feel like a high-quality consumer commerce brand: visual, fast,
reassuring, accessible and easy to use. The tenant administration
experience should feel like a mature SaaS product: clear, efficient,
auditable and safe for business operations.

### 1.2 Business goals

- Launch Lifemac Pharma as the first production-capable tenant after the
  relevant business, product and regulatory reviews.

- Onboard additional businesses using tenant provisioning and
  configuration rather than code forks.

- Support tenant-specific branding, domains, catalogue, customers,
  orders, inventory, payment provider credentials, shipping
  configuration and policies.

- Offer a robust customer shopping journey comparable in breadth to
  leading e-commerce experiences without claiming to reproduce Amazon's
  proprietary systems.

- Keep operational ownership understandable: every service has a bounded
  context and owns its data.

- Develop locally first with repeatable Docker-based dependencies and
  test environments.

- Add AI features only after core commerce data, APIs, permissions and
  auditability are stable.

### 1.3 Product principles

1.  **Tenant isolation by default:** tenant identity is derived and
    verified by the backend; clients cannot choose another tenant by
    changing a request parameter.

2.  **Service data ownership:** only a service may mutate its own
    database.

3.  **Secure payment boundary:** raw cardholder data never enters
    application servers, logs, database, queue, cache or analytics.

4.  **Configurable, not forked:** tenant differences are configuration,
    content and feature entitlements, not tenant-specific branches in
    shared code.

5.  **Premium UX:** design quality, accessibility, responsive behavior
    and state handling are acceptance criteria, not final polish.

6.  **Small implementation increments:** AI coding agents work from
    approved, bounded tasks and must explain changed code and tests.

7.  **Evidence before completion:** a feature is not complete because
    code was generated; it must pass tests and explicit acceptance
    criteria.

8.  **Local-first, production-aware:** local setup must resemble future
    production boundaries without prematurely selecting hosting vendors.

### 1.4 Non-goals for the initial release

- A public marketplace where unrelated third-party sellers list products
  in one shared storefront.

- Microservices deployed to cloud infrastructure during the initial
  development phase.

- Azure services, managed cloud databases, cloud object storage or
  hosted AI services as prerequisites.

- AI diagnosis, medical advice, prescriptions or automated treatment
  recommendations.

- Storing, processing or transmitting raw PAN, CVV/CVC, PIN or
  magnetic-stripe data in platform application systems.

- A mobile application in the first release; the storefront must be
  mobile-first and installable/PWA support may be assessed later.

- A promise of automatic legal, tax, pharmaceutical or PCI compliance
  without professional validation.

## 2. Users, actors and tenancy model

### 2.1 Platform actors

| Actor                     | Scope                           | Typical permissions                                                                                                    |
|---------------------------|---------------------------------|------------------------------------------------------------------------------------------------------------------------|
| Platform Super Admin      | Entire SaaS control plane       | Create/suspend tenants, assign plans, provision databases, configure platform capabilities, view platform audit events |
| Platform Support Operator | Approved support scope          | View tenant operational status and support diagnostics; no unrestricted customer/payment data access                   |
| Tenant Owner              | One tenant                      | Manage tenant settings, invite staff, configure storefront and business operations                                     |
| Tenant Admin              | One tenant                      | Manage most store operations according to assigned permissions                                                         |
| Catalogue Manager         | One tenant                      | Products, categories, variants, images and content                                                                     |
| Inventory Manager         | One tenant                      | Stock, batch, expiry, warehouse and stock adjustments                                                                  |
| Order Manager             | One tenant                      | Orders, fulfilment, cancellations and return workflows                                                                 |
| Finance Operator          | One tenant                      | Payment status, invoices, refunds subject to policy; no PAN/CVV access                                                 |
| Customer Support Agent    | One tenant                      | Customer and order support with field-level restrictions and audit trail                                               |
| Store Customer            | One tenant storefront at a time | Browse, sign in, purchase, manage profile, addresses, wishlist, reviews and orders                                     |

### 2.2 Tenant identity

A tenant is a business boundary represented by an immutable, opaque
tenant_id. It is not a user-supplied display name. The platform resolves
a tenant from a verified storefront domain/subdomain or an explicitly
configured local development host mapping. The incoming Host header is
not trusted by itself; only configured and verified domain mappings are
accepted.

Every request entering a tenant-scoped service must carry a tenant
context created by a trusted gateway/BFF or service authentication
layer. The receiving service validates the context and the caller's
service identity. A client-supplied tenant_id is never sufficient
authorization.

### 2.3 Tenant data isolation model

**Required model: dedicated logical PostgreSQL database per tenant per
service.** In local development, these logical databases may run inside
one local PostgreSQL Docker container for convenience, but each database
remains a separate database with separate credentials/roles and
migration lifecycle. Future production topology may distribute databases
across separate PostgreSQL instances or clusters without changing the
ownership model.

Examples (names are illustrative; use opaque IDs in actual
infrastructure):

- platform_control_plane — platform-owned metadata only.

- identity_tenant\_\<opaque-id\> — that tenant's customer/staff
  identities, memberships, profiles and authentication metadata.

- catalog_tenant\_\<opaque-id\> — that tenant's products, categories,
  variants and product content.

- pricing_tenant\_\<opaque-id\> — that tenant's prices, coupons and
  campaigns.

- inventory_tenant\_\<opaque-id\> — that tenant's stock, batches,
  warehouses and reservations.

- cart_tenant\_\<opaque-id\> — that tenant's carts and cart items.

- orders_tenant\_\<opaque-id\> — that tenant's orders and order-line
  snapshots.

- payments_tenant\_\<opaque-id\> — that tenant's payment intents,
  provider references, transaction events and refund records; never raw
  card data.

Each service has its own database credentials that can connect only to
the service-owned databases it is responsible for. Credentials must not
be shared among services. The platform control plane does not hold
tenant database passwords in plaintext. It stores non-secret database
routing/provisioning identifiers and references to secrets. Local
development secrets live in ignored local secret files/environment
variables; production secret storage is selected in the hosting phase.

### 2.4 Tenant provisioning lifecycle

1.  Platform Super Admin creates a tenant with legal/business name,
    desired slug, owner contact and selected plan.

2.  Tenant status is PENDING_SETUP.

3.  Provisioning workflow allocates a tenant identifier and creates
    service-owned tenant databases/roles for the services enabled for
    that tenant.

4.  Each service applies its own versioned migrations and validates
    connectivity.

5.  Default tenant settings, feature entitlements and initial admin
    invitation are created.

6.  Domain/subdomain is registered. Custom domains remain
    PENDING_VERIFICATION until ownership is verified.

7.  Readiness checks pass; tenant becomes ACTIVE.

8.  Suspension blocks new storefront transactions and admin actions
    according to policy while preserving data for retention/export
    obligations.

9.  Tenant offboarding supports export, retention hold, approved
    deletion and auditable completion.

Provisioning must be idempotent and resumable. A failure must not leave
a tenant marked active with partially provisioned services. Provisioning
status is tracked per service and per database. Database creation and
migrations must be auditable.

### 2.5 Cross-tenant identity

Tenant customer accounts are tenant-scoped. The same email or mobile
number may exist independently in different tenant identity databases.
There is no implicit shared customer profile across stores. Platform
employees use a separate platform identity boundary. A future optional
single sign-on experience may link identities through an explicit
consented identity-broker design; it must not silently merge tenant
customer records.

## 3. Scope and functional requirements

Priority definitions: **P0** = release blocker/core; **P1** = expected
first full commerce release; **P2** = later enhancement. Features
involving medicines or regulated products remain disabled until product
classification and legal/licence requirements are validated for the
tenant and jurisdiction.

### 3.1 Platform control plane and SaaS administration

| ID       | Priority | Requirement                                                                                                  |
|----------|----------|--------------------------------------------------------------------------------------------------------------|
| PLAT-001 | P0       | Platform Super Admin can create, view, update lifecycle status and suspend a tenant.                         |
| PLAT-002 | P0       | Tenant receives immutable opaque ID, unique store slug and lifecycle status.                                 |
| PLAT-003 | P0       | Provisioning creates a dedicated database for every enabled service for that tenant.                         |
| PLAT-004 | P0       | Platform records service/database provisioning state and supports retry/resume safely.                       |
| PLAT-005 | P0       | Platform stores tenant-to-domain mapping; unverified/unknown domains cannot resolve to a tenant.             |
| PLAT-006 | P0       | Platform has a separate control-plane database containing metadata only, not tenant commerce records.        |
| PLAT-007 | P1       | Platform supports tenant plan/feature entitlements and tenant-specific feature flags.                        |
| PLAT-008 | P1       | Platform supports tenant-level limits (users, products, storage, orders) with clear enforcement behavior.    |
| PLAT-009 | P1       | Platform provides an auditable support-access workflow with purpose, approval, expiry and least privilege.   |
| PLAT-010 | P1       | Platform supports tenant export, retention hold and deletion workflow.                                       |
| PLAT-011 | P2       | Platform supports self-service onboarding, plan changes, invoices and SaaS subscription billing.             |
| PLAT-012 | P2       | Platform supports tenant usage metering and operational health views without exposing another tenant's data. |

### 3.2 Storefront branding and content configuration

- Tenant name, logo, favicon, brand colors, typography tokens and
  approved theme presets.

- Configurable home page modules: hero banner, category tiles, featured
  collection, best sellers, new arrivals, promotions, editorial content
  and trust information.

- Header, footer, navigation and contact details.

- Custom domain and platform subdomain.

- Tenant-specific locale, currency, time zone, tax configuration and
  legal/policy content.

- Feature entitlements decide which optional modules are visible.

- Design tokens are validated; arbitrary tenant-supplied CSS/JavaScript
  is prohibited in the standard plan.

- Configuration changes are previewable, versioned and auditable;
  published configuration can be rolled back.

### 3.3 Customer identity and authentication

P0/P1 customer authentication capabilities:

- Guest browsing and guest cart.

- Registration and login using email + password.

- Email verification and secure password reset.

- Mobile number verification and OTP login where a compliant SMS
  provider is configured.

- Google sign-in using OpenID Connect authorization code flow with PKCE.

- Optional email OTP or magic-link login after anti-abuse controls are
  in place.

- Account profile and contact preferences.

- Multiple delivery addresses, one default address and address
  validation hooks.

- Active session listing, logout current session and revoke all
  sessions.

- Account deletion/deactivation workflow subject to order, tax and legal
  retention requirements.

- Tenant-scoped staff invitations and role assignment.

Security requirements:

- Passwords are hashed with Argon2id using a reviewed,
  production-appropriate configuration and unique salts; passwords are
  never reversibly encrypted or logged.

- OTPs are random, short-lived, single-use, stored hashed,
  attempt-limited and invalidated after use. They are never logged.

- Login, registration, password reset, OTP issue/verify and OAuth
  callback endpoints have layered abuse controls: IP, account
  identifier, tenant, device/session signals and progressive cooldowns.
  Do not reveal whether an email/phone is registered.

- OAuth uses exact redirect URI allowlists, state and nonce validation
  as appropriate, PKCE S256, issuer/audience/signature checks, replay
  prevention and secure linking rules. No implicit grant or
  resource-owner password grant.

- Browser sessions use Secure, HttpOnly and appropriately SameSite
  cookies over HTTPS in production; CSRF protection is required for
  cookie-authenticated state-changing operations. Avoid persistent
  access tokens in browser localStorage.

- Admin accounts require MFA before production access; high-risk actions
  require step-up authentication.

- Access tokens are short-lived; refresh/session credentials are
  rotated, revocable and stored hashed where applicable.

- Account enumeration, credential stuffing, brute-force, session
  fixation, CSRF, XSS, OAuth account-linking and IDOR/BOLA tests are
  required.

### 3.4 Catalogue and product information

- Product, category, subcategory, brand, collection and attribute
  management.

- SKU and barcode fields; product variants (pack size, size, quantity,
  flavor/type where relevant).

- Product title, short and long description, images, product video
  reference, selling unit and status.

- MRP/list price and tenant-configured selling price; discounts are
  owned by Pricing service.

- Ingredients, directions for use, precautions, warnings, storage,
  manufacturer/marketer details and regulatory information where
  applicable.

- Cosmetic/drug/other regulated product classification and tenant-level
  category restrictions.

- Product visibility, scheduled publication and draft preview.

- Product image alt text and responsive renditions.

- Product detail page with availability, delivery estimate, variants,
  reviews and related products.

- Import/export in a controlled CSV format with schema validation and
  error report.

- No unverified medical, therapeutic, dermatological or efficacy claims
  may be generated or published automatically.

For medicines, prescriptions and regulated products, implement only
after jurisdiction-specific legal and licensing review. The initial
store can launch with eligible cosmetics/personal-care products if the
tenant has the required manufacturing/marketing and labelling
permissions. Product category eligibility must be configuration-driven
and fail closed when required evidence is missing.

### 3.5 Search and discovery

- Keyword search with typo tolerance and autocomplete.

- Filters by category, price, availability, attributes and supported
  product characteristics.

- Sort by relevance, price, newest and tenant-approved popularity.

- Product suggestions and related products.

- Search service maintains a tenant-partitioned index or physically
  separated per-tenant index namespace with strict access and deletion
  controls; source of truth remains Catalogue service.

- Search documents must not leak other tenants' product content. Tenant
  ID is a mandatory index filter and index lifecycle includes per-tenant
  deletion/rebuild.

- AI semantic search is deferred to the AI phase; initial search is
  deterministic and explainable.

### 3.6 Pricing, promotions and tax

- Tenant-owned currency and pricing configuration.

- MRP, selling price, scheduled price changes and product/variant
  pricing.

- Coupon codes, campaign rules, first-order discounts, product/category
  discounts, minimum basket value, usage limits, per-customer limits and
  expiry.

- Promotion stacking rules must be explicit and deterministic.

- Tax calculation is adapter-based and jurisdiction-specific. Do not
  hard-code tax rates in frontend code or treat a generic percentage as
  legal tax advice.

- Cart and checkout must show a line-item breakdown: item price,
  discount, tax, shipping, fees and final payable amount.

- Price is revalidated server-side at checkout; the browser's submitted
  total is never trusted.

### 3.7 Inventory and fulfilment stock

- Tenant-specific warehouses/locations.

- Stock on hand, reserved, available and damaged quantities.

- Stock movements with actor, reason, source reference and timestamp.

- Low-stock thresholds and alerts.

- Batch/lot number, manufacturing date, expiry date and recall/hold
  status where relevant.

- FEFO (first-expiry-first-out) picking policy where required by product
  category and tenant policy.

- Reservation with expiry/TTL to prevent overselling.

- Concurrency-safe stock decrement and release.

- Inventory adjustments require permission, reason and audit record.

- Returns must not automatically re-enter sellable stock;
  inspection/disposition is required.

### 3.8 Cart and wishlist

- Guest cart and authenticated cart.

- Merge guest cart after login with deterministic conflict rules.

- Cart persistence across sessions/devices for authenticated customers.

- Add/remove/update quantity, save for later, wishlist and move wishlist
  item to cart.

- Validate product status, tenant, price and stock before checkout.

- Recalculate totals on server; cart cache is not the source of
  financial truth.

- Tenant-aware Redis keys; no cart key can be read across tenants or
  accounts.

### 3.9 Checkout and address

- Checkout supports guest and signed-in customers according to tenant
  policy.

- Address selection/create, delivery options, shipping charges, coupon
  application and final order summary.

- Server-side eligibility checks for product category, quantity, stock,
  customer location, age/prescription rules if later applicable.

- Inventory reservation and pricing quote are time-bounded.

- Checkout uses an idempotency key to prevent duplicate order/payment
  creation.

- User explicitly confirms final amount and key terms before payment.

- Checkout failures recover safely and explain the next action without
  exposing internal errors.

### 3.10 Payments and card-data boundary

**Mandatory card-data design:**

1.  Integrate a payment service provider (PSP) through an adapter.
    Support a sandbox provider first; select the India production
    provider only after commercial, banking and compliance evaluation.

2.  Use provider-hosted checkout or hosted fields/tokenized components
    so PAN and CVV are submitted directly to the PSP, not to platform
    backend services.

3.  Do not create API request fields, database columns, queue messages,
    logs or analytics properties for raw PAN, CVV/CVC, PIN, PIN block or
    track data.

4.  Persist only payment metadata required for reconciliation and
    customer display: tenant ID, order/payment IDs, provider name,
    provider payment/intent reference, status, amount, currency,
    timestamps, payment method category, card brand and last four digits
    if supplied by provider, and a provider token/reference only when
    needed and protected as a secret.

5.  Display card metadata as Brand •••• 1234. Do not reconstruct or
    attempt to unmask a card number.

6.  Never store CVV/CVC after authorization, even encrypted. Never
    request CVV for a stored-card or recurring flow unless the PSP's
    compliant transaction flow collects it directly for the specific
    authorization; our systems must not retain it.

7.  Verify payment webhooks using provider signature verification over
    the required raw request body, timestamp/replay protections where
    available, and idempotent event processing.

8.  Treat browser redirects as UX signals only; payment state is
    confirmed server-to-server with the PSP.

9.  Reconcile payment and order status; handle late, duplicate,
    out-of-order and failed webhooks.

10. Never log payment tokens, authorization secrets, full provider
    payloads containing sensitive fields or payment credentials.

Payment features:

- UPI and supported local payment methods through PSP.

- Cards through hosted PSP UI.

- Net banking/wallets where PSP supports them.

- Cash on delivery only when enabled and permitted by
  tenant/product/shipping policies.

- Payment intent/order creation, authorization/capture/void, failure,
  timeout and reconciliation.

- Full/partial refund and refund status.

- Payment transaction history and invoice/receipt references.

- Multiple PSP configurations per tenant if needed, but each tenant's
  merchant credentials and settlement account remain isolated.

- Platform SaaS subscription billing is a separate bounded context from
  customer checkout payments. Do not mix tenant subscription revenue and
  tenant product-sale settlement.

**Merchant-of-record decision:** for the white-label model, the default
assumption is each tenant supplies/connects its own merchant/PSP account
and receives its own settlement. A platform-managed
split-settlement/marketplace model is a separate business/legal/payment
design and is not assumed.

The use of hosted payment fields/tokenization can reduce direct handling
of card data, but it does not automatically make the merchant or
platform PCI DSS compliant or remove all payment-security obligations.
Confirm the applicable PCI scope/SAQ with the PSP, acquirer and
qualified assessor before production.

### 3.11 Orders, cancellations, returns and refunds

- Order history, order detail, invoice, delivery status and reorder.

- Order state machine with valid transitions and audit history.

- Immutable order-line snapshot of product name, SKU, variant, unit
  price, discount, tax, quantity and applicable terms at purchase time.

- Cancellation eligibility by state and tenant policy.

- Return/replacement request with reason, evidence and status.

- Return eligibility rules configurable by product type and legal
  policy; regulated products may have restrictions.

- Refunds are executed through Payment service and linked to original
  payment references.

- Order service owns order lifecycle; payment status remains
  authoritative in Payment service and is synchronized via API/event.

- Support agents cannot edit financial totals or mark a payment
  successful manually.

### 3.12 Shipping and delivery

- Tenant-specific origin/warehouse and shipping configuration.

- Provider adapter for shipping aggregators/carriers.

- Serviceability check, shipping rate/ETA quote, label/manifest
  creation, pickup, tracking updates and delivery proof where supported.

- Shipment exceptions, lost/damaged package workflow and delivery
  failure handling.

- Customer tracking page and notifications.

- Shipping provider credentials are encrypted/secrets-managed and
  tenant-scoped.

- Manual fulfilment mode for local development and initial pilot.

### 3.13 Reviews, support and customer communication

- Verified-purchase reviews, star rating, moderation and abuse
  reporting.

- Product Q&A with tenant moderation.

- Contact/support request and case history.

- Transactional email/SMS/WhatsApp adapter with consent and opt-out
  preferences where applicable.

- Notification templates are tenant-branded and versioned.

- Notifications are queued and retried; duplicate sends are prevented
  with idempotency keys.

- Marketing consent is separate from transactional message permissions.

### 3.14 Tenant administration and business analytics

- Dashboard KPIs: orders, sales, refunds, conversion funnel, inventory
  alerts and fulfilment status.

- Product/category management, image/content management, bulk
  import/export.

- Orders and fulfilment workbench.

- Customer support view with field masking and least-privilege roles.

- Coupon/campaign management.

- Team/member management, role/permission management and audit log.

- Tenant configuration, branding, domain, policies, payment and shipping
  adapters.

- Reports export with tenant scoping and data minimization.

- Analytics are tenant-specific. Platform-level aggregated metrics must
  be anonymized/aggregated and must not reveal raw tenant customer data
  without an explicit, lawful, contractually permitted support/analytics
  basis.

## 4. Non-functional requirements

### 4.1 Security

Security is a release requirement. The implementation must use OWASP
ASVS 5.0.0 as the primary application security verification baseline,
with relevant OWASP API Security Top 10 risks mapped to test cases. At
minimum:

- Threat model at the platform, tenant, identity, payment, admin and
  event boundaries.

- Strong tenant authorization and service-to-service authentication.

- Least-privilege database roles and service identities.

- Secure secret handling and rotation; no secrets committed to Git or
  embedded in container images.

- Input validation at every trust boundary; parameterized SQL/ORM
  queries.

- Output encoding and safe rich-text sanitization.

- CSRF protection for cookie-authenticated state changes; CSP and
  security headers for browser apps.

- CORS allowlists; production HTTPS and secure cookie settings.

- Rate limits, abuse controls and resource quotas.

- Secure file upload validation, content-type/signature checks, size
  limits, malware scanning strategy before production, safe object/file
  names and non-executable storage.

- Webhook signature validation and replay/idempotency controls.

- Audit logging for privileged and financial actions; logs must not
  contain passwords, OTPs, session tokens, PAN/CVV or secret values.

- Dependency pinning, vulnerability scanning, SBOM generation, container
  image scanning and patch policy.

- SAST, secret scanning, DAST and penetration testing before production
  release.

- Backup encryption and tested restore; tenant-specific
  restore/export/delete process.

- Data retention and deletion rules by data category and jurisdiction.

**No zero-vulnerability guarantee:** passing automated scans is not
proof that an application is vulnerability-free. Security sign-off
requires reviewed evidence and an explicit accepted-risk record for
known residual findings.

### 4.2 Availability, reliability and resilience

- Services must have bounded timeouts, retry budgets, circuit breakers
  where appropriate and graceful failure behavior.

- Do not retry non-idempotent operations blindly.

- Use idempotency keys for payments, order creation, refunds and webhook
  processing.

- Database transactions must be short and scoped to a single service
  database.

- Cross-service workflows use sagas/compensating actions rather than
  distributed database transactions.

- Event consumers must be idempotent and tolerate duplicate/out-of-order
  events.

- Dead-letter handling and replay procedure required for durable events.

- Health endpoints: liveness and readiness are distinct.

- Graceful shutdown must stop accepting work and finish/return in-flight
  work safely.

- Backup and recovery objectives are set before production hosting;
  tenant-level restore must be proven.

### 4.3 Performance and scalability

Initial targets are engineering goals, to be validated with realistic
load tests before launch:

- Storefront key pages should target LCP \<= 2.5 seconds at the 75th
  percentile for an agreed test profile, with INP \<= 200 ms and CLS \<=
  0.1 where measurable.

- Typical read APIs should target p95 \<= 300 ms excluding third-party
  provider latency; checkout/payment endpoints have separate
  provider-aware budgets.

- No unbounded list endpoints; pagination and bounded page sizes are
  mandatory.

- Database indexes and query plans are reviewed for high-volume access
  paths.

- Redis is a cache, not the system of record. Cache invalidation must be
  event- or version-driven and safe under tenant separation.

- Per-tenant quotas and rate limits prevent noisy-neighbor resource
  exhaustion.

- Search indexes, media storage and caches must be tenant-aware and
  support per-tenant cleanup.

- Horizontal scaling is a later hosting concern; services must remain
  stateless where practical.

### 4.4 UX, accessibility and compatibility

- Mobile-first responsive design across common phone, tablet and desktop
  sizes.

- Target WCAG 2.2 AA for user-facing workflows, subject to formal
  accessibility review.

- Keyboard navigation, visible focus, accessible labels, alt text,
  contrast and screen-reader semantics.

- Every interactive page defines loading, empty, error, success,
  disabled and permission-denied states.

- Checkout has clear progress, price breakdown, error recovery and no
  surprise fees.

- Product details make ingredients, usage, warnings and availability
  easy to locate.

- Use a documented design system and tenant design tokens; do not create
  one-off styles for a tenant.

### 4.5 Maintainability and operability

- Each service has independent README, dependency manifest/lock,
  configuration, migrations, API contract, tests, Dockerfile and
  release/version metadata.

- OpenAPI contracts are versioned and generated client types are not
  handwritten copies.

- Event schemas are versioned and backward compatibility is enforced.

- Structured logs, metrics and traces include correlation IDs and tenant
  IDs only where safe; sensitive data is redacted.

- Local development can start required dependencies using documented
  commands.

- Configuration is environment-based and validated at startup.

- Architecture decisions are recorded in ADRs.

## 5. Target architecture

### 5.1 Logical architecture

                        CUSTOMER STOREFRONT (Next.js)
                                   |
                         Storefront BFF / API Edge
                                   |
           +-----------------------+-------------------------+
           |                       |                         |
      Identity Service       Catalogue Service         Cart Service
           |                       |                         |
     Identity DB per        Catalogue DB per            Cart DB per
     tenant                 tenant                      tenant
           |                       |                         |
           +----------- versioned APIs / domain events ------+
                                   |
           +-----------------------+-------------------------+
           |             Commerce Services                    |
           | Pricing | Inventory | Checkout | Payment | Order |
           | Shipping/Fulfilment | Reviews | Notifications    |
           +-----------------------+-------------------------+
                                   |
                       Kafka event backbone (when needed)
                                   |
                   Search indexing / analytics / workers

     TENANT ADMIN (Next.js) ---- Tenant Admin BFF / API Edge
     PLATFORM CONSOLE --------- Platform Control Plane Service
                                          |
                                Platform Control DB
                      (tenant registry, domains, plans, provisioning)

The diagram is logical, not a final network topology. Local Docker
Compose may run the services and PostgreSQL databases on one developer
machine while preserving their logical ownership boundaries.

### 5.2 Microservice boundaries and ownership

| Service                | Owns                                                                                        | Must not own                                                        |
|------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| Platform Control Plane | Tenant registry, tenant lifecycle, domains, plans, entitlements, provisioning orchestration | Products, customers, carts, orders, payment card data               |
| Identity & Access      | Tenant-local customer/staff identity, credentials, sessions, memberships and permissions    | Product/order/inventory tables                                      |
| Catalogue              | Products, categories, variants, product attributes and product content                      | Prices, stock quantities, orders                                    |
| Pricing & Promotions   | Price rules, coupons, campaigns and discount evaluation                                     | Product master or payment transactions                              |
| Inventory              | Warehouses, stock, batches, expiry, reservations and movements                              | Orders or payment records                                           |
| Cart                   | Guest/authenticated carts, cart items and wishlist                                          | Final orders or payment status                                      |
| Checkout Orchestrator  | Checkout session, quote snapshot and workflow coordination                                  | Card data or service-owned product/inventory source tables          |
| Payment                | Payment intents, PSP adapter, transaction state, refunds and provider webhook inbox         | Raw PAN/CVV or order master data                                    |
| Orders                 | Orders, immutable line snapshots, order state and cancellation/return case references       | Payment credentials or inventory source tables                      |
| Shipping & Fulfilment  | Shipments, labels, carrier events and tracking                                              | Order source data beyond references/snapshots needed for fulfilment |
| Search & Discovery     | Search documents/index and discovery telemetry                                              | Source-of-truth product records                                     |
| Reviews & Content      | Reviews, ratings, Q&A and tenant content modules                                            | Identity credentials or order source database                       |
| Notifications          | Notification templates, delivery attempts, preferences and provider adapters                | Customer password/authentication secrets                            |
| Media                  | Media metadata, upload authorization and tenant-scoped asset references                     | Arbitrary executable files or card images                           |
| Analytics/Reporting    | Derived, minimized reporting datasets                                                       | Authoritative commerce state                                        |

Service boundaries can be adjusted through ADRs before implementation.
They must not be collapsed simply to simplify an AI-generated change
without an approved architecture decision.

### 5.3 Generic monorepo structure: frontend and backend are separate roots

The repository and extracted project folder must use a generic name such
as commerce-saas-platform/. Do not name the repository, root directory,
package namespace or shared platform after Lifemac or any future tenant.
Lifemac Pharma appears only as an example tenant in seed data, test
fixtures and documentation.

Keep frontend and backend as separate top-level workspaces. Frontend
applications and shared UI packages live only under frontend/.
Independently structured backend microservices, service-owned
migrations, service contracts and backend tests live only under
backend/. Cross-cutting local infrastructure is under infra/; product
and architecture documents are under docs/.

    commerce-saas-platform/
    ├── AGENTS.md
    ├── README.md
    ├── Makefile
    ├── .gitignore
    ├── .env.example
    ├── docs/
    │   ├── product/PRD.md
    │   ├── architecture/
    │   ├── adr/
    │   ├── api/
    │   ├── events/
    │   ├── agent-prompts/
    │   └── runbooks/
    ├── frontend/
    │   ├── README.md
    │   ├── package.json                 # created after Phase 0 toolchain ADR approval
    │   ├── pnpm-workspace.yaml             # created after Phase 0 toolchain ADR approval
    │   ├── turbo.json                   # created after ADR approval; frontend task orchestration
    │   ├── apps/
    │   │   ├── storefront/              # customer shopping website
    │   │   ├── tenant-admin/            # tenant business console
    │   │   └── platform-console/        # SaaS Super Admin console
    │   ├── packages/
    │   │   ├── ui/                      # neutral reusable primitives
    │   │   ├── design-tokens/           # theme tokens and schema
    │   │   ├── api-client/              # generated API clients only
    │   │   ├── frontend-config/         # lint, TS and build config
    │   │   └── test-utils/
    │   └── tooling/
    ├── backend/
    │   ├── README.md
    │   ├── services/
    │   │   ├── platform-control-plane/
    │   │   ├── identity-access/
    │   │   ├── catalogue/
    │   │   ├── pricing-promotions/
    │   │   ├── inventory/
    │   │   ├── cart/
    │   │   ├── checkout-orchestrator/
    │   │   ├── payment/
    │   │   ├── orders/
    │   │   ├── shipping-fulfilment/
    │   │   ├── search-discovery/
    │   │   ├── reviews-content/
    │   │   ├── notifications/
    │   │   ├── media/
    │   │   └── analytics-reporting/
    │   ├── contracts/
    │   │   ├── openapi/
    │   │   └── events/
    │   ├── tests/
    │   │   ├── integration/
    │   │   ├── contract/
    │   │   ├── tenant-isolation/
    │   │   └── security/
    │   └── tooling/
    ├── infra/
    │   ├── local/
    │   │   ├── compose.yaml                     # PostgreSQL, Redis and Mailpit default local dependencies
    │   │   ├── RabbitMQ via optional messaging profile; Kafka deferred until a separate event-stream ADR
    │   │   ├── postgres/init/
    │   │   ├── redis/
    │   │   ├── mailpit/
    │   │   └── observability/
    │   └── scripts/
    ├── quality/
    │   ├── e2e/
    │   ├── visual-regression/
    │   └── security-checks/
    ├── scripts/
    └── .github/
        └── workflows/

The actual starter archive must include the directory tree above, using
short README.md files and .gitkeep placeholders where no implementation
exists yet. Empty folders alone are not preserved by Git or ZIP tools.
Do not pre-generate all services' runtime code during Phase 0; create
executable scaffolding only when that individual service reaches its
approved implementation task.

**Frontend application structure (each app owns its routes and
features):**

    frontend/apps/storefront/
    ├── README.md
    ├── public/
    ├── src/
    │   ├── app/                         # route entry points/layouts
    │   ├── features/                    # catalogue, search, cart, checkout, account
    │   ├── components/                  # app-specific composition
    │   ├── lib/                         # tenant resolution client, API, analytics
    │   └── styles/
    └── tests/

tenant-admin/ and platform-console/ follow the same app-level pattern
but retain their own route trees, features, access guards and tests. Do
not put all three apps into one Next.js application with a large
role-based conditional UI. Shared UI primitives may be reused from
frontend/packages/ui; tenant branding is driven by validated tenant
design tokens and must not be hardcoded into shared components.

**Backend microservice internal structure (repeat independently per
service):**

    backend/services/catalogue/
    ├── README.md
    ├── pyproject.toml                   # created when this service is scaffolded
    ├── uv.lock                          # service-specific dependency lock
    ├── Dockerfile                       # service-specific build boundary
    ├── migrations/                      # owned only by this service
    ├── src/catalogue/
    │   ├── api/                         # routes, schemas, auth/context dependencies
    │   ├── application/                 # use cases and orchestration
    │   ├── domain/                      # entities, value objects, rules
    │   ├── infrastructure/              # repositories, DB, external adapters
    │   └── config/                      # validated runtime configuration
    └── tests/
        ├── unit/
        ├── integration/
        ├── contract/
        └── security/

Every service has its own Python package namespace, dependency manifest
and lockfile, Dockerfile, health/readiness checks, configuration schema,
database migrations, tests, README, API contract and release/build
command. Do not create a single backend app/ that contains all business
modules and merely labels them microservices. Do not share ORM models,
repositories, domain entities or direct database credentials between
services. Shared backend code is limited to versioned API/event
contracts and small reviewed infrastructure utilities; business rules
remain in their owning service.

**Service ownership summary:**

| Backend service        | Owns its tenant database(s)                                              | Main responsibility                                                     |
|------------------------|--------------------------------------------------------------------------|-------------------------------------------------------------------------|
| Platform Control Plane | One platform control-plane DB (not a tenant commerce DB)                 | Tenant registry, domains, plans, entitlements and provisioning metadata |
| Identity & Access      | One identity DB per tenant                                               | Customer/staff identities, memberships, credentials and sessions        |
| Catalogue              | One catalogue DB per tenant                                              | Products, categories, variants and product content                      |
| Pricing & Promotions   | One pricing DB per tenant                                                | Prices, coupons, campaigns and discount rules                           |
| Inventory              | One inventory DB per tenant                                              | Stock, warehouses, batches, expiry and reservations                     |
| Cart                   | One cart DB per tenant                                                   | Guest/authenticated carts, items and wishlist                           |
| Checkout Orchestrator  | One checkout DB per tenant                                               | Checkout sessions, quote snapshots and saga coordination state          |
| Payment                | One payment DB per tenant                                                | PSP references, payment intents, webhook inbox and refunds; no PAN/CVV  |
| Orders                 | One orders DB per tenant                                                 | Orders, immutable line snapshots and order lifecycle                    |
| Shipping & Fulfilment  | One fulfilment DB per tenant                                             | Shipments, carrier events, labels and tracking                          |
| Search & Discovery     | One search DB/index per tenant                                           | Tenant-isolated search documents and discovery data                     |
| Reviews & Content      | One reviews/content DB per tenant                                        | Ratings, reviews, Q&A and tenant content                                |
| Notifications          | One notifications DB per tenant                                          | Templates, preferences and delivery attempts                            |
| Media                  | One media metadata DB per tenant                                         | Tenant-owned asset metadata and authorization                           |
| Analytics & Reporting  | One reporting DB per tenant or explicitly partitioned tenant-owned store | Derived reports and minimized analytics data                            |

The exact initial service list and whether a service is provisioned
immediately or lazily must be approved as ADRs. The isolation invariant
does not change: tenant business data is never placed in one shared
database table across tenants.

### 5.3.1 How to work service-by-service

Use a dependency-led sequence, not a random file-by-file sequence.
Complete one bounded service milestone, prove its isolation and
contracts, then move to the next service. Do not attempt to generate all
microservices in one agent task.

Recommended backend implementation order:

1.  **Platform Control Plane:** tenant registration, verified local
    domain mapping, tenant lifecycle, provisioning orchestration and
    service-database registry. It owns only platform metadata.

2.  **Identity & Access:** tenant-local customer/staff identity, secure
    login/session flows, OAuth/OTP adapters and authorization contracts.

3.  **Catalogue:** tenant-specific product/category/variant CRUD and
    public browse APIs.

4.  **Media:** safe product media upload/reference lifecycle, with
    tenant-scoped storage paths and validation.

5.  **Pricing & Promotions:** authoritative price/discount calculation
    and coupon rules.

6.  **Inventory:** tenant-specific stock, batch/expiry, reservation and
    concurrency controls.

7.  **Cart:** guest/authenticated cart, merge, wishlist and server-side
    recalculation triggers.

8.  **Orders:** order aggregate, immutable purchase snapshots and order
    state machine.

9.  **Payment:** PSP sandbox adapter, hosted checkout/tokenization
    boundary, signed webhooks, idempotency and refunds. Integrate with
    checkout only after its contracts are approved.

10. **Checkout Orchestrator:** coordinate quote, stock reservation,
    order creation and payment saga/compensation using APIs/events;
    never own other services' source tables.

11. **Shipping & Fulfilment:** shipment creation, tracking and return
    logistics.

12. **Notifications:** tenant-branded transactional messages and retry
    handling.

13. **Search & Discovery:** tenant-scoped indexing, filters and
    relevance.

14. **Reviews & Content:** verified-purchase reviews, Q&A and tenant
    content modules.

15. **Analytics & Reporting:** derived, minimized, permission-filtered
    reporting.

The Phase 0 architecture review may adjust this order when dependencies
demand it. The agent must document the reasoning and obtain human
approval before changing the sequence.

For each service, follow the same completion loop:

- Read its bounded context, PRD requirements, accepted ADRs and
  upstream/downstream contracts.

- Write/approve its service design and API/event contract before
  implementation.

- Scaffold only that service with its own package, dependencies, config,
  Dockerfile, migrations, health endpoint, tests and README.

- Design its tenant database provisioning and per-service
  least-privilege credentials.

- Implement domain rules and use cases before transport/integration
  glue.

- Add unit tests, service integration tests, contract tests and
  tenant-isolation/security tests.

- Run the service locally in isolation, then integrate it with one
  approved upstream/downstream service.

- Demonstrate the end-to-end user/business flow and failure paths.

- Complete code walkthrough, update documentation and obtain human
  approval before starting the next service.

Frontend implementation is also separated from backend ownership. First
establish the frontend workspace and design-token system. Then build the
Platform Console onboarding path, followed by the tenant storefront
shell and tenant admin shell. Implement storefront features against
stable, versioned backend APIs one vertical user journey at a time:
browse product, product detail, account, cart, checkout, order tracking.
Never create duplicate business logic in the frontend.

### 5.3.2 Workspace and build boundaries

- Frontend uses a single frontend-only pnpm workspace; Turborepo may
  orchestrate frontend app/package tasks after approval. Do not put
  Python services in pnpm workspaces.

- Backend services retain individual Python packaging/lock boundaries.
  Root Makefile/scripts provide convenience orchestration but must call
  a service's own documented commands.

- Each service can be built, tested, versioned, containerized and
  released independently. A monorepo path change must not force all
  services to rebuild.

- Local Docker Compose may start the required dependencies and selected
  services; provide optional profiles rather than requiring the entire
  platform to run for every task.

- CI should detect changed paths and run the affected service plus
  relevant contract, integration and tenant-isolation suites.

### 5.4 Monorepo rules

- A single repository does not mean a single deployable application.

- Each service can be built, tested, versioned and packaged
  independently.

- No direct import of another service's domain, ORM model, repository or
  database module.

- Shared packages contain only stable cross-cutting contracts/utilities;
  they must not become a dumping ground for business logic.

- Cross-service communication uses versioned HTTP APIs or versioned
  event contracts.

- Each service owns its schema migrations and database role.

- A service may publish domain events only after committing its own
  state using an outbox pattern.

- Contract changes require compatibility checks and consumer tests.

- CI should run affected-service tests plus shared contract and
  tenant-isolation suites.

- A change touching multiple services must describe the reason,
  API/event impact, rollout order and rollback behavior.

### 5.5 Data ownership and database topology

**Required logical topology:**

- One control-plane database for platform metadata.

- For each tenant and each tenant-data service, one dedicated logical
  PostgreSQL database owned by that service.

- A service-specific database role for every database; no cross-service
  credentials.

- No shared tenant tables for products, prices, carts, customers,
  inventory, orders or payments.

- No cross-database foreign keys or SQL joins. IDs and references are
  exchanged through APIs/events.

- Each service has independent migrations and connection pools.

**Tenant database resolver:**

- Resolve the tenant from trusted host/domain mapping at the edge, then
  propagate a signed/internal tenant context.

- Validate tenant status and caller membership/entitlement.

- Resolve service database location from trusted platform metadata.

- Retrieve credentials from the configured secret provider; local
  development uses ignored environment files.

- Create a tenant-scoped connection/session for that service only.

- Reject unknown, suspended, provisioning or incomplete tenants for
  ordinary traffic.

- Never use a raw request query/body/header tenant ID to select
  arbitrary database credentials.

**Provisioning safety:**

- Database and role identifiers are generated from opaque IDs, not raw
  tenant names.

- Database credentials are unique, least privilege and rotated.

- Migrations run as a dedicated migration identity; runtime role has no
  schema-owner/superuser privileges.

- Database creation, migration and deprovisioning are auditable.

- Failed provisioning is retryable and cannot cause an active/partially
  migrated tenant.

- Backups and restore are tenant/service scoped and tested.

### 5.6 Cache and local infrastructure

Redis is allowed for cache, rate-limit counters, short-lived
sessions/OTP state and carefully designed ephemeral coordination. It is
not the source of truth for prices, payments, order status or inventory.

- Every cache key includes tenant identity and resource identity, e.g.
  tenant:{tenant_id}:catalog:product:{product_id}:v{version}.

- Redis ACL/users are separated by service where practical; sensitive
  values are not cached unless justified and protected.

- Cache TTLs, invalidation and stampede protection are defined per use
  case.

- Cache failure must fall back safely to authoritative service/database
  behavior for critical operations.

- Never cache card PAN/CVV or payment secrets.

Kafka may be introduced as a local Docker image using KRaft mode when
asynchronous domain events are needed. Kafka is an event-stream
backbone, not a universal replacement for a task queue. If a specific
background-job queue is needed, choose a queue technology based on
delivery, acknowledgement, delay and retry semantics; document it in an
ADR rather than adding Kafka by default.

When Kafka is used:

- Publish versioned domain events, not ORM/database rows.

- Use transactional outbox for reliable publish-after-commit.

- Consumers are idempotent and track processed event IDs.

- Define retry topics/backoff and dead-letter topics.

- Include event ID, schema version, occurred-at, tenant ID, aggregate ID
  and correlation/causation IDs.

- Never place secrets, raw card data or unnecessary PII in events.

- Partition keys must preserve required aggregate ordering without
  mixing tenant data in an unsafe way.

- Tenant offboarding includes per-tenant event/index/cache cleanup and
  retention policy.

### 5.7 Local development runtime

Initial local dependencies may be run in Docker Compose:

- PostgreSQL container (logical database-per-tenant-per-service;
  separate roles).

- Redis container.

- Mailpit local SMTP capture in the default Phase 1A profile.

- Optional RabbitMQ messaging profile only when an approved background-job use case exists.

- Kafka is deferred until a reviewed ADR establishes a replayable/high-volume event-streaming requirement; it is not part of the default local stack.

- Local object/file storage adapter for product images and documents.

- Optional observability profile for OpenTelemetry collector, Prometheus
  and Grafana after core service logging is established.

The Phase 1A Compose baseline starts only PostgreSQL 18.7, Redis 8.10.3 and Mailpit 1.33.1, bound to loopback. RabbitMQ is optional. No frontend or microservice is started by default. Development data is synthetic. Production/customer data must never be copied to local fixtures. Secrets are generated into Git-ignored `.env` and `infra/local/secrets/redis.conf` by `scripts/bootstrap_local.py`; safe sample files contain no credentials.

## 6. Service interaction and critical workflows

### 6.1 API and service communication

- REST/JSON with OpenAPI for initial synchronous APIs.

- Internal service authentication with distinct service identity and
  short-lived credentials; tenant context is integrity-protected.

- API gateway/BFF performs edge routing and aggregation but does not own
  business data.

- Explicit timeouts, retry policies and request correlation IDs.

- Use asynchronous events for decoupled side effects (search indexing,
  notifications, analytics, inventory/order integration).

- Avoid synchronous fan-out chains on customer-facing paths; checkout is
  orchestrated with bounded calls and stateful recovery.

### 6.2 Checkout/order/payment saga

The controlling sequence is defined in
docs/architecture/CHECKOUT_PAYMENT_SAGA.md. The normal flow is:

1.  Storefront submits a checkout attempt with an idempotency key. The
    backend resolves tenant context and verifies the shopper/guest
    policy.

2.  Checkout validates cart ownership, product/variant publication
    status, current server-side prices, coupons, tax configuration and
    delivery eligibility. Browser totals are never authoritative.

3.  Inventory atomically reserves stock with a bounded expiry and
    returns a reservation reference.

4.  Pricing/Checkout freezes an immutable quote snapshot: line
    quantities, unit prices, discounts, tax breakdown, shipping,
    currency, total and expiry.

5.  Orders creates a durable PENDING_PAYMENT order idempotently before
    any PSP redirect. The order stores immutable purchase snapshots and
    the reservation/quote references.

6.  Payment creates a PSP payment intent/session for that exact order,
    amount and currency using an idempotency key, then returns only a
    hosted checkout URL/reference.

7.  The shopper enters card/UPI details only on the PSP-hosted
    page/fields. PAN/CVV never pass through the platform.

8.  Payment validates provider webhook signature over the
    provider-required raw body, deduplicates the event, checks merchant
    account/order/amount/currency/reference and reconciles
    server-to-server where appropriate.

9.  Payment records its state and outbox event in one local transaction.
    The Checkout saga resumes from the durable event/inbox state.

10. Orders transitions from PENDING_PAYMENT to the valid paid/confirmed
    state; Inventory commits the reservation idempotently. Fulfilment
    and notifications are requested through contracts/events.

11. Browser return/redirect is a UX signal only. The storefront fetches
    authoritative order/payment state from backend APIs.

Failure handling must cover failed/cancelled/late payment, duplicate and
out-of-order webhooks, expired reservations, unavailable
Orders/Inventory services, refund/void failures and manual
reconciliation. Never mark payment successful from a browser redirect;
never mark a refund complete before PSP confirmation. Do not hold a
database transaction open while calling a PSP or carrier API.

### 6.3 Event examples

- TenantProvisioningRequested.v1

- TenantProvisioned.v1

- ProductPublished.v1

- PriceChanged.v1

- InventoryReserved.v1

- InventoryReservationExpired.v1

- PaymentAuthorized.v1

- PaymentFailed.v1

- PaymentRefunded.v1

- OrderPlaced.v1

- OrderCancelled.v1

- ShipmentCreated.v1

- ShipmentDelivered.v1

- ReviewSubmitted.v1

Events are illustrative. The event catalogue and schema compatibility
policy must be approved before coding.

## 7. High-level domain model

### 7.1 Platform control-plane data

- Tenant: opaque ID, legal name, display name, slug, lifecycle status,
  created/updated timestamps.

- TenantDomain: hostname, verification status, primary flag, tenant
  reference.

- TenantPlan: plan/entitlement reference, limits and effective dates.

- TenantServiceProvisioning: service, database identifier, state,
  migration version, health state, secret reference.

- TenantFeatureEntitlement: feature key, enabled state, limits and
  effective period.

- PlatformAdmin, PlatformRole, PlatformAuditEvent.

No tenant product/customer/order/payment records are stored here.

### 7.2 Tenant service data (illustrative)

| Service       | Main aggregates/entities                                                                                   |
|---------------|------------------------------------------------------------------------------------------------------------|
| Identity      | Customer, StaffUser, Credential, ExternalIdentity, Membership, Role, Permission, Session, Address, Consent |
| Catalogue     | Product, Variant, Category, Attribute, ProductMedia, Ingredient, ProductDocument, ProductStatus            |
| Pricing       | PriceList, Price, Promotion, Coupon, Redemption, TaxQuoteReference                                         |
| Inventory     | Warehouse, StockItem, Batch, StockMovement, Reservation, RecallHold                                        |
| Cart          | Cart, CartItem, Wishlist, WishlistItem                                                                     |
| Checkout      | CheckoutSession, Quote, DeliveryOption, CheckoutAttempt, SagaState                                         |
| Payment       | PaymentIntent, ProviderAccountReference, PaymentAttempt, ProviderEvent, Refund, ReconciliationRecord       |
| Orders        | Order, OrderLineSnapshot, OrderAddressSnapshot, OrderStatusHistory, Cancellation, ReturnCase               |
| Shipping      | Shipment, Package, LabelReference, TrackingEvent, CarrierAccountReference                                  |
| Reviews       | Review, Rating, Question, Answer, ModerationAction                                                         |
| Notifications | Template, Preference, DeliveryAttempt, SuppressionRecord                                                   |
| Media         | Asset, Rendition, UploadSession, AccessPolicy                                                              |

All tenant-owned entities remain in the tenant's service-owned database.
Service-owned IDs are opaque and globally unique where practical;
references across services are identifiers only, not database-level
foreign keys.

## 8. Authentication, authorization and account safety

### 8.1 Authorization model

Use RBAC for tenant staff roles, with permission checks at API/use-case
level. Add resource attributes where needed (e.g. assigned warehouse,
order ownership, support scope). Deny by default. Enforce authorization
on every object-level operation, not only in UI navigation.

Customer access must be scoped to the authenticated customer and tenant.
Staff access must be scoped to tenant membership and role. Platform
support access is separate, time-limited and audited.

### 8.2 Session and account controls

- Secure session issuance, rotation, expiry and revocation.

- Refresh token reuse detection if refresh tokens are used.

- Device/session metadata minimized and protected.

- Logout invalidates server-side session/refresh token.

- Account recovery must not bypass MFA for admins.

- Sensitive actions (change email/phone, payment settings, refund, staff
  role change, domain change) require re-authentication or step-up MFA.

- Admin access requires MFA; enforce strong recovery codes and recovery
  policy.

### 8.3 Security tests

- Password storage and reset tests.

- OAuth state/nonce/PKCE, redirect allowlist and account-linking tests.

- OTP expiry, replay, brute-force and rate-limit tests.

- Session fixation, logout revocation, refresh rotation and CSRF tests.

- Tenant switch/host spoofing tests.

- Object-level authorization/IDOR tests for products, carts, orders,
  addresses, reviews and admin APIs.

- Staff privilege escalation tests.

- Suspended tenant and provisioning-state access tests.

## 9. Payment security and PCI-aware requirements

### 9.1 Stored payment metadata allowlist

Allowed only where needed, returned by the PSP and reviewed for PCI
scope:

- PSP name and account reference.

- PSP payment intent/transaction ID.

- Payment method type (card, UPI, net banking, etc.).

- Card brand/network label.

- Last four digits of PAN for display.

- Expiry month/year only if provided and necessary for a saved-method
  display; do not store unless there is a real product need and the
  PSP/acquirer approves the design.

- Provider token/payment-method reference only if required for future
  payments and protected as a secret with customer consent and
  PSP-supported flow.

### 9.2 Prohibited data

- Full PAN.

- CVV/CVC/CID after authorization (must never be retained by platform
  systems).

- PIN/PIN block.

- Track data or equivalent chip data.

- Raw card form request bodies in application logs, APM traces, crash
  reports, analytics, support tickets, chat transcripts, screenshots or
  event payloads.

Do not build a custom card-entry form unless it is a PSP-hosted
field/SDK that sends data directly to the PSP and the integration has
been reviewed. Do not write code that masks a raw PAN after it has
already passed through our API; the correct design prevents the raw data
from entering our systems in the first place.

### 9.3 Payment operations safeguards

- Payment state transitions validated server-side.

- Webhook signature validation and replay control.

- Idempotent order/payment/refund commands.

- Reconciliation for unmatched PSP transactions.

- Refund amount never exceeds refundable captured amount.

- Dual approval/step-up for high-value refunds if tenant policy requires
  it.

- Audit actor, reason and reference for every refund/manual financial
  action.

- Sandbox/test cards only in local development; never production card
  data.

## 10. Observability, audit and operational controls

- Structured JSON logs with timestamp, service, environment, correlation
  ID, trace ID, safe tenant ID and outcome.

- Redaction library shared across services; tests verify no password,
  OTP, token, PAN/CVV or provider secret is logged.

- Metrics: request rate, latency, error rate, DB pool saturation,
  migration state, cache health, event lag, retry/DLQ count, payment
  webhook delay and order saga status.

- Distributed traces across API and event workflows with sensitive
  attributes excluded.

- Audit logs are append-only from application perspective and record
  actor, tenant, action, resource, outcome, timestamp and correlation
  ID. Do not place secret values or raw payment details in audit data.

- Local observability profile can be introduced incrementally;
  production alerting and log retention are defined in the hosting
  phase.

## 11. Testing and quality gates

### 11.1 Required test layers

- Unit tests for domain rules and use cases.

- Integration tests against real PostgreSQL/Redis/Kafka containers as
  appropriate (not only mocks).

- API tests from OpenAPI contracts.

- Service contract tests for all service-to-service APIs/events.

- Tenant isolation tests with at least two tenants and attempts to
  cross-read, cross-write, cache-poison and spoof tenant context.

- Authentication and authorization security tests.

- Payment sandbox tests: success, decline, timeout, duplicate webhook,
  invalid signature, out-of-order event, partial refund and
  reconciliation.

- End-to-end storefront tests: anonymous browse, signup/login, Google
  OAuth test mode, search, cart, address, checkout, payment sandbox,
  order status, cancellation/return.

- Admin E2E tests for tenant configuration, product creation, stock
  update, order fulfilment and audit events.

- Visual regression/accessibility tests for core screens.

- Load tests for browse/search/cart/checkout and tenant noisy-neighbor
  scenarios.

- Backup/restore and tenant export/delete tests before production.

### 11.2 Definition of Done for every phase/task

A task is complete only when:

1.  The approved acceptance criteria are met.

2.  The implementation follows the service's ownership boundary.

3.  Tests are added/updated and pass; relevant security and
    tenant-isolation tests pass.

4.  API/event/database contract changes are documented and backward
    compatibility is considered.

5.  Migrations are reversible or have a documented forward-recovery
    plan.

6.  No secrets or sensitive payment data are introduced.

7.  Error, loading, empty and permission states are handled in UI.

8.  Logs and metrics are safe and useful.

9.  The service README/run instructions are updated.

10. Codex/agent provides a change summary, files touched, tests run,
    risks and an explanation of important code paths.

11. Human review is completed before merging.

## 12. Phased implementation roadmap

Hosting and AI are intentionally later. Each phase ends with a
demonstrable, tested milestone and a human approval gate.

### Phase 0 — Architecture baseline (technical work completed)

**Status:** The controlling architecture package is prepared in
docs/architecture/PHASE_0_ARCHITECTURE_BASELINE.md, supported by the
service catalogue, ADRs, threat model, tenant data-isolation document,
corrected checkout saga, portability guidance and open-decisions
register.

Completed technical outputs:

- C4 system context and container/application boundaries.

- Generic tenant model and database-per-tenant-per-service topology.

- Service ownership, API/event boundaries and service-by-service
  dependency order.

- Trusted tenant resolution, separate user/service authentication and
  privilege boundaries.

- Database provisioning, independent service migrations, credential and
  pool-management requirements.

- Corrected pending-order-before-payment saga and payment-data
  prohibition.

- Threat model, verification baseline and service Definition of Done.

- Local-first/EC2 portability strategy and remaining business/compliance
  decision register.

**Exit state:** Technical baseline is complete; human approval remains
required. Merchant-of-record, PSP vendor, tax, regulated product
eligibility, privacy/retention, scale/SLO, RPO/RTO and production
hosting decisions remain open and are not guessed. They do not block
local dependency setup or the initial Control Plane foundation.

### Phase 1A — Local developer foundation

**Goal:** create a repeatable local environment without requiring the
developer to run every microservice or install databases directly on
Windows.

Deliverables already prepared in this repository:

- Generic monorepo roots and coding-agent rules.

- Docker Compose dependencies: PostgreSQL 18.7, Redis 8.10.3 and Mailpit
  1.33.1 by default.

- Optional RabbitMQ 4.4.0 messaging profile; Kafka deferred until an
  approved stream/replay use case.

- Generated local .env with unique credentials, Git ignore and
  loopback-only host ports.

- Separate bootstrap, runtime, migrator, low-privilege Control Plane
  worker and database-provisioner identities.

- Local setup runbook and health/configuration commands.

The developer must execute and verify Phase 1A locally. Do not scaffold
all services or start the optional broker stack by default. See
docs/architecture/PHASE_1_LOCAL_FOUNDATION.md.

**Exit gate:** Compose config validates, only PostgreSQL/Redis/Mailpit
are healthy, .env is ignored, role boundaries are verified and actual
local results are recorded.

### Phase 1B — Platform Control Plane only

**Goal:** implement the first backend service and prove tenant lifecycle
and isolated database provisioning for two synthetic tenants.

Scope:

- backend/services/platform-control-plane/ only, with its independent
  FastAPI project, lockfile, migrations, tests and Dockerfile.

- Metadata-only platform_control database, tenant registry,
  verified-domain state, lifecycle, provisioning jobs and secret
  references.

- A separate privileged provisioning worker; the public HTTP API never
  receives database/role creation credentials.

- Idempotent provisioning of an isolated tenant/service database and
  distinct runtime/migrator credentials; revoke PostgreSQL
  CONNECT/TEMPORARY from PUBLIC and grant connection only to that
  service DB's roles.

- A separate low-privilege Control Plane worker DB role for
  provisioning-job updates.

- Owning-service migration execution remains the responsibility of that
  owning service's migration runner; Control Plane must not run other
  services' migrations.

- Local domain fixture, negative isolation tests and
  recovery/fault-injection tests.

**Exit gate:** two synthetic tenants are provisioned into separate
opaque test databases for one fixture service; cross-tenant/service
credentials are rejected; unknown/unverified/suspended/partially
provisioned tenants fail closed; provisioning is idempotent/recoverable;
API contract, runbook and tests pass; human approval is recorded. Only
then can Identity & Access begin.

After Phase 1B approval, Identity & Access is the next backend service
in the service catalogue. It remains a separate implementation task with
its own database, dependencies, migrations and security gate. The
frontend design-system phase may proceed as its own approved frontend
task without bundling Identity into the Control Plane.

### Phase 2 — Design system, storefront shell and tenant administration shell

**Goal:** deliver polished branded experiences with dynamic theme
resolution.

Deliverables:

- Design tokens and reusable UI library.

- Storefront and tenant admin shells.

- Platform console shell.

- Tenant theme/configuration API integration.

- Responsive navigation, home page module framework, footer and reusable
  product card skeleton.

- Loading/empty/error states, accessibility baseline and visual
  regression harness.

Exit gate: two tenants render different branded storefront themes from
configuration without conditional hardcoding of tenant names.

### Phase 3 — Identity, customer accounts and staff access

**Goal:** secure identity and account management for tenant customers
and staff.

Deliverables:

- Tenant-scoped identity database provisioning.

- Email/password, email verification and password recovery.

- Mobile OTP adapter and abuse protection.

- Google OIDC login with authorization code + PKCE.

- Secure session management and logout/revocation.

- Tenant staff invitation, RBAC and admin MFA.

- Security tests for OAuth, OTP, account enumeration, session, CSRF and
  IDOR.

Exit gate: authentication works independently per tenant; cross-tenant
session/account access tests fail closed.

### Phase 4 — Catalogue and product discovery

**Goal:** enable tenant-specific product setup and storefront browsing.

Deliverables:

- Catalogue service/database per tenant.

- Product/category/variant/media management.

- Tenant admin product CRUD and import validation.

- Public catalogue APIs and storefront listing/detail pages.

- Search/filter/sort baseline.

- Product information/regulated-category metadata and publication
  checks.

Exit gate: Lifemac and sample tenant have independent products, assets
and catalogue operations.

### Phase 5 — Pricing, inventory, cart, wishlist and order core

**Goal:** implement tenant-specific pricing, stock-aware shopping and
the durable order aggregate needed by checkout.

Deliverables:

- Pricing/Promotion service and tenant database.

- Inventory service with stock/batch/expiry/reservation model.

- Cart service and tenant database.

- Guest cart, authenticated cart merge, wishlist and save-for-later.

- Orders service foundation with immutable order-line purchase snapshots
  and a minimal order state machine.

- Server-side pricing and availability recalculation.

- Concurrency, idempotency and tenant-isolation tests.

Exit gate: no overselling in tested concurrent reservation cases; cart
cannot cross tenants/customers; order creation is idempotent and stores
a stable purchase snapshot.

### Phase 6 — Payment and checkout orchestration sandbox

**Goal:** complete a secure checkout flow using the already-approved
order, pricing and inventory contracts, without live card handling.

Deliverables:

- Payment service with one PSP sandbox adapter and its tenant-specific
  database.

- Hosted checkout/hosted fields/tokenization integration; no raw PAN/CVV
  reaches platform APIs.

- Checkout Orchestrator service/database and versioned saga state.

- Idempotency, signed webhook verification, refund sandbox flow and
  reconciliation.

- Outbox/event handling and compensation paths for payment failure,
  stock release and order state changes.

- Payment security logging tests and an allowlisted payment metadata
  schema.

- Checkout failure recovery and accessibility.

Exit gate: payment sandbox and checkout saga test suites pass; security
review verifies no raw card data in application requests, databases,
logs, events, cache or analytics.

### Phase 7 — Order lifecycle completion, fulfilment, returns and notifications

**Goal:** complete the customer-visible and operational order lifecycle
on top of the order core built in Phase 5 and checkout/payment flow
built in Phase 6.

Deliverables:

- Complete order state transitions, customer order history and staff
  order operations.

- Inventory/payment saga compensation and reconciliation for delayed,
  duplicate and failed events.

- Manual fulfilment first, then carrier adapter.

- Shipment tracking, delivery exceptions, cancellation,
  return/replacement and refund workflows.

- Tenant-branded transactional notifications with retries and delivery
  audit.

Exit gate: end-to-end order scenarios pass, including payment failure,
delayed/duplicate webhook, cancellation, partial refund, delivery
exception and return workflows.

### Phase 8 — Commerce operations and launch readiness

**Goal:** complete the full tenant business console and prove the
platform is safe to launch for approved products.

Deliverables:

- Reviews/Q&A, reporting, customer support view, coupons/campaigns and
  CMS/homepage management.

- Role/permission review and audit logging.

- Product batch/expiry/recall workflows for applicable categories.

- SEO, consent and policy pages.

- Performance, accessibility, load and disaster-recovery tests.

- Security assessment and issue remediation.

- Tenant onboarding/offboarding and backup/restore drills.

Exit gate: launch checklist signed off; regulated product eligibility
confirmed; no unresolved critical/high security findings without formal
risk acceptance.

### Phase 9 — AI capabilities

**Goal:** add AI as a controlled enhancement over verified
tenant-specific commerce data.

Potential features:

- Tenant-scoped RAG product assistant.

- Semantic product search.

- Product comparison and evidence-grounded recommendations.

- Customer support agent using permission-checked order APIs.

- AI-assisted product content draft with human approval.

- Admin sales/inventory insights.

Requirements:

- Every retrieval/query is tenant-scoped and tested for cross-tenant
  leakage.

- Tool calls use least-privilege service APIs and customer
  authorization.

- No AI agent may directly query tenant databases or initiate
  payment/refund/order changes without policy checks and explicit
  confirmation.

- Prompt injection, data exfiltration, hallucination, unsafe medical
  advice and tool abuse are tested.

- Medical diagnosis/prescribing and unsupported claims are prohibited.

Exit gate: evaluations show acceptable grounding, tenant isolation,
safety and action authorization.

### Phase 10 — Hosting and production deployment

**Goal:** select hosting based on capacity, operational model,
compliance and cost after local architecture is proven.

Deliverables:

- Hosting decision and infrastructure architecture.

- TLS/domain/DNS, network segmentation, ingress and WAF strategy.

- Production secrets management and key management.

- Database deployment, connection pooling, backup/restore and
  tenant-level recovery.

- CI/CD, image registry, deployment and rollback.

- Monitoring, alerting, incident response, patching and on-call
  runbooks.

- Security testing, penetration test and final payment/compliance
  validation.

Exit gate: production readiness review and business approval. Hosting
vendor is deliberately not chosen in this PRD.

## 13. Initial API surface (illustrative)

APIs are service-owned and versioned. This list is a domain map, not a
final OpenAPI contract.

| Domain           | Example endpoints                                                                                                                                                                |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Platform tenants | POST /platform/v1/tenants, GET /platform/v1/tenants/{tenantId}, POST /platform/v1/tenants/{tenantId}/provision, POST /platform/v1/tenants/{tenantId}/suspend                     |
| Domains/themes   | POST /platform/v1/tenants/{tenantId}/domains, GET /storefront/v1/tenant-config                                                                                                   |
| Identity         | POST /identity/v1/register, POST /identity/v1/login, POST /identity/v1/otp/request, POST /identity/v1/otp/verify, POST /identity/v1/oauth/google/start, POST /identity/v1/logout |
| Catalogue        | GET /catalogue/v1/products, GET /catalogue/v1/products/{productId}, POST /admin/catalogue/v1/products, PATCH /admin/catalogue/v1/products/{productId}                            |
| Pricing          | POST /pricing/v1/quotes, POST /pricing/v1/coupons/validate                                                                                                                       |
| Inventory        | GET /inventory/v1/availability, POST /inventory/v1/reservations, POST /inventory/v1/reservations/{id}/release                                                                    |
| Cart             | GET /cart/v1, POST /cart/v1/items, PATCH /cart/v1/items/{itemId}, DELETE /cart/v1/items/{itemId}                                                                                 |
| Checkout         | POST /checkout/v1/sessions, POST /checkout/v1/sessions/{id}/confirm                                                                                                              |
| Payments         | POST /payments/v1/intents, POST /payments/v1/webhooks/{provider}, POST /payments/v1/refunds                                                                                      |
| Orders           | GET /orders/v1, GET /orders/v1/{orderId}, POST /orders/v1/{orderId}/cancel, POST /orders/v1/{orderId}/returns                                                                    |
| Shipping         | GET /shipping/v1/quotes, POST /shipping/v1/shipments, GET /shipping/v1/shipments/{id}/tracking                                                                                   |

Sensitive routes require strict authorization, idempotency and audit
behavior. Public storefront endpoints are still tenant-scoped and
rate-limited.

## 14. Environment and configuration standards

- local, test, staging and production configuration profiles are
  distinct.

- Local .env files are ignored by Git; .env.example contains no real
  secrets.

- Application settings are validated at startup; missing required
  configuration fails fast.

- Tenant configuration is data with schema/version validation, not
  arbitrary environment variables.

- Service-to-service credentials are unique per service and environment.

- No production credentials or payment-provider live keys are used in
  local development.

- Use synthetic seed data with at least two tenants for tenant-isolation
  testing.

## 15. Coding-agent operating contract

The coding agent must treat this PRD and the accepted ADRs as project
constraints. It must not autonomously redesign the platform or implement
multiple phases in one task.

### 15.1 Mandatory behavior

1.  Read AGENTS.md, this PRD, relevant service README and accepted ADRs
    before changing code.

2.  State the target phase, exact task, assumptions, files likely to
    change and tests before implementation.

3.  If a requirement conflicts with an accepted architecture decision,
    stop and propose an ADR; do not silently choose the easier
    implementation.

4.  Implement only the approved task. Do not generate unrelated services
    or speculative features.

5.  Do not create a shared multi-tenant products/users/orders database.
    Tenant business data is database-per-tenant-per-service.

6.  Do not let one service import another service's
    ORM/domain/repository code or access its database.

7.  Do not accept a client-supplied tenant ID as the source of
    authorization or database routing.

8.  Never add raw card, CVV, password, OTP, refresh token or secret
    fields to logs, database records, events or analytics.

9.  Never implement custom card data collection; use the approved PSP
    hosted/tokenized flow.

10. Do not add Azure/cloud resources or hosting deployment before Phase
    10 is approved.

11. Do not add AI features before Phase 9 is approved.

12. Run tests and report exact commands/results; never claim tests
    passed if they were not run.

13. Provide an explanation of important code paths, data ownership,
    security checks and trade-offs so the human reviewer can understand
    the change.

14. Keep changes small, reviewable and formatted; do not rewrite
    unrelated files.

15. Add or update tests for tenant boundaries, authorization and failure
    modes with every relevant feature.

### 15.2 Required output after every coding task

- Summary of what changed.

- Phase/task and acceptance criteria addressed.

- Files added/modified/deleted.

- Data model/migration changes and rollback/forward-recovery plan.

- API/event contract changes.

- Security/tenant-isolation considerations.

- Tests run with exact commands and outcomes.

- Known limitations and unresolved risks.

- A plain-language explanation of how the code works.

- Suggested next task only; do not implement it without approval.

### 15.3 Current Codex entry point: Phase 1A local foundation

Phase 0 technical architecture documents are already prepared. Do not
regenerate another architecture review or redesign the system. Start
with docs/agent-prompts/PHASE_1A_LOCAL_FOUNDATION.md to inspect and
validate the prepared local Compose foundation, generate the local .env
only if absent, and run the default dependencies. Do not scaffold
application services during Phase 1A.

After the user confirms Phase 1A health checks and records the results,
use docs/agent-prompts/PHASE_1B_PLATFORM_CONTROL_PLANE.md. Implement
only the Platform Control Plane, in bounded increments, and stop at its
human approval gate. Do not begin Identity & Access automatically.

## 16. Product decisions requiring explicit approval

The technical architecture and initial service boundaries are documented
in the controlling Phase 0 baseline. The remaining business, compliance
and operations decisions are recorded in
docs/architecture/OPEN_DECISIONS_REGISTER.md; agents must not resolve
them by guessing. Key open items include merchant-of-record/settlement,
PSP vendor, product eligibility, tax jurisdiction, privacy/retention,
SaaS subscription billing, tenant count/concurrency, RPO/RTO and EC2
topology. These do not block local Phase 1A or the metadata/provisioning
foundation, but affected production capabilities must remain disabled
until decisions are approved.

## 17. Risks and mitigations

| Risk                                                | Mitigation                                                                                                                                                                     |
|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Tenant data leakage                                 | Dedicated tenant DB per service, trusted tenant context, isolated credentials, object-level auth, cross-tenant adversarial tests                                               |
| Too many databases/connection pools                 | Start with a controlled service set, connection pooling, database provisioning automation, capacity tests and tiered future topology without reverting to shared tenant tables |
| Microservice complexity                             | Keep bounded contexts explicit, begin with a minimal vertical slice, use contract tests and avoid unnecessary synchronous chains                                               |
| Payment data accidentally captured                  | PSP-hosted card UI, deny-list request/log fields, no PAN/CVV schema, automated log/event scans and payment-flow review                                                         |
| Payment replay/duplicate order                      | Idempotency keys, signed webhooks, event deduplication and reconciliation                                                                                                      |
| AI agent makes unauthorized changes                 | Defer AI; later use scoped tools, user confirmation, policy engine, audit trail and evaluations                                                                                |
| Regulated products/claims                           | Product classification, legal/licence review, publication gates, approved product data and prohibited medical advice                                                           |
| Noisy tenant affects others                         | Per-tenant quotas, rate limits, resource monitoring, queue isolation strategy and capacity testing                                                                             |
| Cache/search/event leakage                          | Mandatory tenant partitioning, authorization filters, tenant cleanup and isolation tests                                                                                       |
| Agent-generated insecure code                       | AGENTS.md guardrails, small tasks, mandatory tests, human review, ASVS control mapping and security gates                                                                      |
| Local development mistaken for production readiness | Separate launch checklist; TLS, secrets, backups, monitoring, penetration testing and incident response required before public launch                                          |

## 18. Acceptance criteria for the first foundation milestone

The first implementation milestone is considered successful only when
all of the following are demonstrated locally:

1.  A platform admin creates two synthetic tenants.

2.  Platform metadata is stored in the control-plane database only.

3.  At least one fixture tenant-data service provisions separate
    databases for both tenants; a second service key is tested to prove
    the service dimension of isolation.

4.  Each service has credentials restricted to its own tenant databases;
    PostgreSQL PUBLIC has no CONNECT/TEMPORARY rights on those
    databases.

5.  A request for Tenant A cannot select Tenant B's database by changing
    URL, body, header or query values.

6.  Unknown, unverified, suspended and partially provisioned tenants are
    denied appropriately.

7.  A database credential for Tenant A cannot connect to Tenant B's
    database.

8.  Migrations run independently for each service and tenant.

9.  Tenant theme/domain configuration resolves correctly for two local
    storefront hosts.

10. Logs contain safe correlation/tenant identifiers but no credentials
    or customer secrets.

11. Automated isolation tests pass and include negative attack cases.

12. The local developer setup is documented and can be recreated from a
    clean checkout.

## 19. Glossary

- **Tenant:** an independently branded business using the SaaS platform.

- **Control plane:** platform-owned system managing tenants, plans,
  domains and provisioning.

- **Data plane:** tenant-facing commerce services that perform
  storefront and business operations.

- **Database-per-tenant-per-service:** a separate database for each
  tenant within each service's data ownership boundary.

- **BFF:** Backend for Frontend; a boundary that shapes APIs for a
  specific UI without owning domain data.

- **PSP:** Payment Service Provider.

- **PAN:** Primary Account Number (card number).

- **CVV/CVC:** Card verification value/code; sensitive authentication
  data.

- **Hosted fields/checkout:** payment-provider UI components that send
  card details directly to the PSP rather than the merchant application.

- **Outbox pattern:** persist domain state and an event record in the
  same service transaction, then publish the event asynchronously.

- **Saga:** a multi-service business workflow with local transactions
  and compensating actions rather than a distributed database
  transaction.

- **ADR:** Architecture Decision Record.

- **RPO/RTO:** Recovery Point Objective / Recovery Time Objective.

## 20. References and security baselines

The following official sources inform the payment and
application-security requirements. They are not a substitute for a
qualified compliance assessment or legal advice.

1.  OWASP Application Security Verification Standard (ASVS) 5.0.0,
    stable release published 30 May 2025: [OWASP ASVS
    5.0.0](https://asvs.owasp.org/)

2.  OWASP API Security Top 10 (2023): [OWASP API Security Top
    10](https://owasp.org/www-project-api-security/)

3.  OWASP Password Storage Cheat Sheet: [OWASP Password Storage Cheat
    Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

4.  IETF RFC 9700, Best Current Practice for OAuth 2.0 Security, January
    2025: [IETF RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)

5.  PCI Security Standards Council FAQ 1319 — CVV/CVC is sensitive
    authentication data and must not be stored after authorization, even
    encrypted: [PCI SSC FAQ
    1319](https://www.pcisecuritystandards.org/faqs/1319/)

6.  PCI Security Standards Council FAQ 1146 — distinction between
    masking displayed PAN and rendering stored PAN unreadable: [PCI SSC
    FAQ 1146](https://www.pcisecuritystandards.org/faqs/1146/)

7.  PCI Security Standards Council FAQ 1071 — PAN display masking
    requirements: [PCI SSC FAQ
    1071](https://www.pcisecuritystandards.org/faqs/1071/)

8.  PCI Security Standards Council FAQ 1318 — data retention and
    disposal requirements and prohibition on storing sensitive
    authentication data after authorization: [PCI SSC FAQ
    1318](https://www.pcisecuritystandards.org/faqs/1318/)

**End of document.** This is the baseline product and architecture
specification. Changes to tenancy isolation, service ownership,
authentication, payment-data handling or delivery sequence require a
reviewed ADR and human approval before implementation.
