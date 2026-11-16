# ADR-003: Database and tenant isolation

- Status: Proposed — human review required
- Decision: PostgreSQL 18.x. Database per tenant per service, provisioned lazily for enabled service/tenant pairs. Singleton platform-control DB stores SaaS metadata only.
- Security: Unique service/tenant runtime and migrator roles; revoke `CONNECT` and `TEMPORARY` from `PUBLIC`; no cross-service SQL/ORM access. Runtime roles are not owners or database/role creators.
- Migrations: Alembic, owned and executed by each service's migration runner. Control Plane provisioning worker creates database/roles and secret references only.
- Operational consequence: Implement bounded lazy connection pools, per-tenant limits, idle eviction, total connection budget, backup/restore and offboarding workflows.
