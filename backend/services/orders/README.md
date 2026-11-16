# Orders

**Status:** Directory placeholder only. Runtime code is intentionally not scaffolded yet.

## Bounded context and data ownership

Tenant orders, immutable order-line snapshots and order state. One orders database per tenant.

## Initial capability scope

Order creation, lifecycle state machine, cancellation/return case references and order query APIs.

## Required independent structure when this service is approved

```text
orders/
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── migrations/
├── src/orders/
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
