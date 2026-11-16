# Inventory

**Status:** Directory placeholder only. Runtime code is intentionally not scaffolded yet.

## Bounded context and data ownership

Tenant warehouses, stock, batches, expiry, reservations and movements. One inventory database per tenant.

## Initial capability scope

Stock availability, reservation/commit/release, batch and expiry operations.

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
