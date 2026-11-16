# Analytics & Reporting

**Status:** Directory placeholder only. Runtime code is intentionally not scaffolded yet.

## Bounded context and data ownership

Tenant-owned derived reporting data with minimization and access controls. One reporting database per tenant or an ADR-approved isolated equivalent.

## Initial capability scope

Sales reports, inventory insights and permission-filtered derived analytics; never authoritative commerce state.

## Required independent structure when this service is approved

```text
analytics-reporting/
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── migrations/
├── src/analytics_reporting/
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
