# ADR-015: Tenant database provisioning

- Status: Proposed — human review required
- Decision direction: Platform Control Plane records tenant lifecycle and provisioning jobs. A separate privileged provisioning worker creates databases, service roles and secret references. It is not exposed through public HTTP routes and does not run owning-service migrations.
- Owning services run their own migration jobs with their own migrator credentials. A tenant is not activated until required databases, migrations and health/smoke checks succeed.
- Open: Production secret manager, SQL privilege boundary/SECURITY DEFINER mechanism, cleanup/rollback semantics and capacity thresholds need detailed design.
