# Backend Service Catalogue

# Part D — Backend Service Catalogue

# Backend service catalogue

Each service is an independently structured backend application under `backend/services/<service-name>/`. The baseline layout is `src/<python_package>/{api,application,domain,infrastructure,config}`, `migrations/`, `tests/{unit,integration,contract,security}/`, `pyproject.toml`, `uv.lock`, `Dockerfile` and `README.md`. A service is not complete until its own build, tests, migration and container work independently.

| Order | Service | Owns | Downstream consumers / integrations | Notes |
|---:|---|---|---|---|
| 1 | `platform-control-plane` | Tenants, domains, lifecycle, plans/entitlements, provisioning jobs and DB/secret references | All tenant-scoped services | No tenant commerce records. Provisioning worker isolated from API credentials. |
| 2 | `identity-access` | Platform operators plus tenant-scoped customer/staff identities, credentials, sessions, memberships and consent | Storefront, tenant admin, platform console and protected APIs | Platform and tenant identity partitions are distinct. |
| 3 | `catalogue` | Product master, categories, variants, attributes, publish state | Storefront, Pricing, Inventory, Search, Reviews | Public reads do not require customer login; admin writes do. |
| 4 | `media` | Asset metadata, processing, ownership and storage refs | Catalogue, storefront, tenant admin | Files are outside the DB; validate, re-encode and authorize access. |
| 5 | `pricing-promotions` | Price lists, coupon rules, campaign evaluation | Cart and Checkout | Server is authoritative; quote snapshots are immutable. |
| 6 | `inventory` | Stock, warehouses, lots/batches, expiry, movements and reservations | Cart availability and Checkout | Atomic reservations; prevent overselling under concurrency. |
| 7 | `cart` | Guest/auth carts, cart lines, wishlist and merge | Storefront and Checkout | Tenant-scoped persistence and guest-to-user merge. |
| 8 | `orders` | Pending/confirmed orders, immutable lines/tax/price snapshots, lifecycle and return cases | Payment, Checkout, Shipping, Notifications | Order exists as PENDING_PAYMENT before hosted PSP checkout. |
| 9 | `payment` | PSP account refs, payment intents/attempts, webhook inbox, refunds and reconciliation | Checkout and Orders | Hosted checkout; no PAN/CVV; tenant-scoped merchant config. |
| 10 | `checkout-orchestrator` | Checkout quotes, workflow/saga state, idempotency and compensation | Cart, Pricing, Inventory, Orders, Payment | Does not own source data from other services. |
| 11 | `shipping-fulfilment` | Shipment state, labels/tracking refs, delivery and return movement | Orders and Notifications | Carrier adapters and signed/idempotent webhooks. |
| 12 | `notifications` | Templates, consent/preference refs, delivery attempts and providers | All services via events | Email/SMS/WhatsApp adapters; retries and suppression. |
| 13 | `search-discovery` | Derived search docs, indexes and relevance metadata | Storefront and Catalogue events | Rebuildable derived data; tenant index isolation. |
| 14 | `reviews-content` | Reviews, ratings, product Q&A and moderation | Storefront, tenant admin | Verified purchase checks use APIs/events, not Orders DB reads. |
| 15 | `analytics-reporting` | Minimized derived data and tenant reports | Tenant admin/platform console with scoped views | No direct source DB reads; retention and privacy controls. |

## Shared technical code policy

Allowed: generated OpenAPI clients, event schema packages, logging/tracing helpers, config parsing, test fixtures and neutral integration utilities.

Not allowed: shared SQLAlchemy models, domain entities, repositories, DB sessions, business rules or direct database credentials across services. A shared library must not make services release-coupled or hide data ownership.

---
