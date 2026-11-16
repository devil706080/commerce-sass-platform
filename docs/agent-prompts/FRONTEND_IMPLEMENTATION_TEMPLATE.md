# Codex Task Template — One Frontend App or Feature

Read root `AGENTS.md`, `docs/product/PRD.md`, the relevant accepted ADRs/contracts and the selected app README.

**Approved phase:** <phase>
**Single app:** <frontend/apps/storefront | tenant-admin | platform-console>
**Task:** <one user journey or screen set>

Before coding, state the UX goal, acceptance criteria, component plan, API contracts, access/tenant context, expected file changes, responsive/accessibility requirements and tests. Stop if backend APIs or design decisions are not approved.

Implement only this app and feature. Do not add backend business logic, database access or authoritative pricing/stock/payment/order calculations to the frontend. Tenant branding comes from validated configuration/design tokens, never hardcoded tenant conditionals. Include loading, empty, error, permission-denied and success states.

Run lint, type checks, unit/component tests and relevant browser/visual checks. Report exact commands/results, explain the interaction and stop for human review.
