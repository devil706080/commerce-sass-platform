# Catalogue

**Status:** Catalogue backend increment implemented: tenant-admin JWT authorization, product CRUD/detail/search, category CRUD, and tenant-isolated `catfx` products/categories storage. Public category reads expose only categories with at least one assigned published product; category filtering uses the category slug. Runtime DDL is owned by the service migration job; API startup does not mutate schema.

## Bounded context and data ownership

Tenant-owned products, categories, variants, product attributes and product content. One catalogue database per tenant.

## Initial capability scope

Product CRUD, publication state, variants, attributes and storefront catalogue APIs.

## Required independent structure when this service is approved

```text
catalogue/
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── migrations/
├── src/catalogue/
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
