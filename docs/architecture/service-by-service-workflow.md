# Service-by-service workflow

## Principles
- One backend service or one frontend app per bounded Codex task.
- Each backend service has its own dependencies, lockfile, config, Dockerfile, migrations, tests and release boundary.
- Each service owns its own tenant/service databases and runs its own migrations.
- Control Plane provisioning creates DBs/roles/secret references; it does not run other services' migrations.
- No cross-service DB/ORM imports or SQL joins. Use versioned APIs/events.

## Backend order
1. Platform Control Plane
2. Identity & Access
3. Catalogue
4. Media
5. Pricing & Promotions
6. Inventory
7. Cart
8. Orders
9. Payment
10. Checkout Orchestrator
11. Shipping & Fulfilment
12. Notifications
13. Search & Discovery
14. Reviews & Content
15. Analytics & Reporting

See `PHASE_0_1_DELIVERY_BLUEPRINT.md` for entry/exit evidence for each service. This order is dependency-aware; it does not authorize implementing all services in one run.

## For every service task
1. Read its README, PRD scope, accepted ADRs and dependencies.
2. Propose API/event contracts and data ownership before code.
3. List files and tests before editing.
4. Implement the smallest vertical slice.
5. Run unit, integration, contract, security and tenant isolation tests appropriate to the slice.
6. Demonstrate a local happy path and failure path.
7. Explain the implementation.
8. Stop for human approval.
