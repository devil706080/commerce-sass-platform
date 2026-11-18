# Tenant administration console

**Status:** Catalogue-management increment implemented. The application provides
an explicit Keycloak login entry point, role-gated access, category management,
product creation, category assignment and publication-state management.

Tenant staff application for catalogue, pricing, inventory, orders, promotions, content, reporting, team and settings. Enforce role/permission-aware navigation and API authorization.

## Expected app structure

```text
tenant-admin/
├── public/
├── src/
│   ├── app/
│   ├── features/
│   ├── components/
│   ├── lib/
│   └── styles/
└── tests/
```

The application calls the Catalogue API only; it never connects to a database.
Orders, delivery, pricing, stock and customer data are intentionally absent until
their owning service contracts exist. A category appears in the storefront only
when a published product is assigned to it.
