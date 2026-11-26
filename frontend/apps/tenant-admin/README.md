# Tenant administration console

**Status:** Catalogue and simplified inventory operations are implemented.

The tenant-specific console provides:

- Keycloak sign-in with tenant membership and role enforcement.
- A dashboard backed by real Catalogue and Inventory data.
- Category management with automatic URL slugs.
- Product creation with pricing, image, categories, opening stock and publishing.
- A default `MAIN` location so staff do not need to configure warehouses.
- Simple stock receipts plus optional batch and expiry tracking.
- Low-stock, out-of-stock and expiry alerts.
- Advanced batch hold and recall controls kept outside the normal daily workflow.

Multiple locations and stock transfers are intentionally marked **Coming soon**. Orders,
customers, payments and revenue will be added only when their owning services provide
real data; the UI does not display placeholder business metrics.

## Ownership boundaries

The browser calls service APIs and never connects directly to a database. Catalogue owns
product content and category assignments. Inventory owns the default location, stock,
batches and reservations. Media owns uploaded image files and metadata. A category is
customer-visible only when it contains a published product.

## Source structure

```text
src/
  app/          Next.js routes and application styling
  components/   Shared presentation components
  features/     Dashboard, catalogue, inventory, authentication and tenant branding
  lib/          Typed API clients and Keycloak integration
```
