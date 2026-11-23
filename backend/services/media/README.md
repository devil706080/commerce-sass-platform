# Media

**Status:** Tenant-scoped image upload runtime implemented for Tenant Admin. JPEG, PNG and WebP
content is validated, decoded, pixel-limited and re-encoded to WebP before storage. Metadata and
files are routed from a short-lived signed tenant context; browser-selected tenant IDs are denied.

## Bounded context and data ownership

Tenant media metadata, upload authorization and asset references. One media metadata database per tenant.

## Initial capability scope

Safe uploads, MIME/content validation, tenant-scoped file references and lifecycle.

## Required independent structure when this service is approved

```text
media/
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── migrations/
├── src/media/
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
