# Inventory

**Status:** Initial backend implemented. The service owns tenant warehouses, SKU stock,
immutable adjustments and atomic reservation/release/commit operations. Runtime requests
require a signed `inventory-api` tenant context and an authorised Keycloak staff token.
The versioned migration is service-owned and runtime startup performs no DDL.

## Bounded context and data ownership

Tenant warehouses, stock, batches, expiry, reservations and movements. One inventory database per tenant.

## Initial capability scope

Stock availability, reservation/commit/release, batch and expiry operations.

## Implemented API

- `GET/POST /api/v1/warehouses`
- `GET/POST /api/v1/stock-items`
- `GET /api/v1/availability/{sku}`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/alerts?type=LOW_STOCK|OUT_OF_STOCK|EXPIRING`
- `POST /api/v1/stock-items/{id}/adjustments`
- `POST /api/v1/stock-items/{id}/receipts`
- `GET /api/v1/stock-items/{id}/movements`
- `GET/POST /api/v1/stock-items/{id}/batches`
- `PATCH /api/v1/stock-items/{id}/batches/{batch_id}/status`
- `POST /api/v1/reservations`
- `GET /api/v1/reservations/{id}`
- `POST /api/v1/reservations/{id}/release`
- `POST /api/v1/reservations/{id}/commit`

Batch receipts increase aggregate stock atomically. Reservations allocate eligible batches
by earliest expiry first (FEFO), can span multiple batches, and release/commit/expiry updates
both aggregate and batch counters. Held, recalled and expired batches are excluded from new
reservations. Checkout service-to-service authorization and real concurrent-database stress
coverage remain required before production checkout integration.

Every migrated tenant receives one idempotently seeded `MAIN / Main Location` warehouse.
Stock items declare either `SIMPLE` or `BATCH_EXPIRY` tracking. Multi-location operations
are intentionally deferred; the current product workflow targets the default location.

## Required independent structure when this service is approved

```text
inventory/
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── migrations/
├── src/inventory/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── config/
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    └── security/
```

## Rules

- This service owns its database schema, migrations, repositories, database credentials and runtime package.
- Provision one dedicated logical database for each tenant served by this service.
- Do not query another service's database or import its domain/ORM/repository code.
- Use versioned HTTP APIs or versioned events for cross-service communication.
- Enforce trusted tenant context, authorization, idempotency and safe logs.
- Add service-specific unit, integration, contract, security and tenant-isolation tests.
- Do not scaffold or implement until its phase/task is explicitly approved.

## Dependencies and contracts

To be defined and approved in Phase 0 ADRs and API/event contracts. Do not guess upstream/downstream dependencies.
