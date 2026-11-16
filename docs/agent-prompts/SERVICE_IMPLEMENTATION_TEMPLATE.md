# Codex Task Template — One Backend Service

Read root `AGENTS.md`, `docs/product/PRD.md`, `docs/architecture/service-by-service-workflow.md`, the selected service README and accepted ADRs/contracts.

**Approved phase:** <phase>
**Single service:** <service path>
**Task:** <one bounded capability>

Before coding, report the requirements, design, expected file changes, dependencies, tenant database boundary, API/event contract, security risks, tests and acceptance criteria. Stop if a needed architecture decision is not approved.

Implement only this service and this capability. Do not change sibling services, frontends, shared contracts or infrastructure unless the approved task explicitly requires it. The service must retain its own package, dependency lock, configuration, Dockerfile, migrations, health checks, README, tests and independent commands.

Enforce database-per-tenant-per-service and a least-privilege DB role. Do not use shared tenant tables or cross-service database access. Do not accept client-supplied tenant IDs as authorization/routing authority. Never handle raw PAN/CVV. Keep secrets and sensitive values out of logs/events/traces.

Add unit, integration, contract, security and tenant-isolation tests appropriate to the task. Run them and report exact commands and actual outcomes. Explain the implementation and stop for human review before proceeding to another service.
