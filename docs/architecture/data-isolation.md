# Tenant data isolation baseline

## Required topology

Tenant commerce data uses **database-per-tenant with schema-per-service**. Example: Tenant A has one opaque tenant database containing `catalogue`, `inventory`, `orders` and `payment` schemas. Tenant B has a different database. The platform control-plane database is separate and stores only SaaS metadata such as tenant registry, verified domain mappings, lifecycle state, plans, entitlements and database provisioning references.

A single local PostgreSQL Docker container may host multiple logical tenant databases for development convenience. Each tenant database is separately named using opaque identifiers, has separate credentials, independent service schemas/migrations and least-privilege roles. Future extraction of a high-scale service into its own database is a later ADR.

## Request-to-database flow

1. Resolve the incoming host against a verified domain mapping in trusted platform metadata.
2. Reject unrecognized, unverified, suspended or incomplete tenants.
3. Authenticate the user/service and validate tenant membership/entitlement.
4. Create signed internal tenant context; never trust raw browser tenant IDs.
5. Resolve only the selected service's database locator and credential.
6. Open a scoped session with that service's tenant database.
7. Authorize the resource operation and emit safe audit/correlation data.

## Prohibited designs

- One shared `products`, `orders`, `customers`, `carts`, `inventory` or `payments` table keyed by `tenant_id`.
- One tenant commerce database shared by all microservices.
- Cross-service SQL joins or direct DB reads/writes.
- A frontend-provided tenant ID used to route to arbitrary database credentials.
- Database identifiers derived directly from untrusted tenant display names.
- Superuser credentials in runtime services.

## Required isolation tests

- Tenant A cannot query or mutate Tenant B's database with Tenant A's credentials.
- A service cannot connect to another service's database.
- URL/body/query/header tampering cannot switch tenant context.
- Unknown, unverified, suspended and partially provisioned tenants fail closed.
- Connection pools do not reuse a connection under the wrong tenant/service context.
- Cache, search, event, media and analytics references are tenant-partitioned.
- Restore, export and offboarding operations remain tenant/service scoped.
