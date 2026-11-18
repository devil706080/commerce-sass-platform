# Catalogue

**Status:** Catalogue backend increment implemented: tenant-admin JWT authorization, product/category CRUD, product-category assignments, image metadata CRUD, variant CRUD, and product price-rule CRUD in tenant-isolated `catfx` storage. Public category reads expose only categories with at least one assigned published product; category filtering uses the category slug; published product image metadata is publicly readable. Runtime DDL is owned by the service migration job; API startup does not mutate schema.

## Current API boundary

- Tenant-admin JWT routes manage products, categories, image metadata, variants and current catalogue price rules.
- Swagger/OpenAPI declares HTTP Bearer JWT authentication, so local staff can use the **Authorize** control with a valid Keycloak access token.
- Public storefront routes expose only published products, qualifying categories and image metadata for published products.
- Image records hold only externally hosted `http`/`https` URLs, alt text and ordering. Upload, malware scanning, transformations and object storage are **not** implemented here; those belong to the future Media service.
- Catalogue price rules are the current local catalogue capability. Checkout pricing must later be calculated by the dedicated Pricing service; a browser must never calculate the final charge.

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
