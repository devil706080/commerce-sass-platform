# Monorepo layout and navigation

## The rule

There are two separate development workspaces: `frontend/` and `backend/`. Each has its own package/tooling conventions. The repository is generic and tenant-neutral; tenant identity and branding are configuration/data, not repository or codebase names.

## Frontend roots

- `frontend/apps/storefront/`: public customer shopping experience. Owns its routing, feature composition and UI tests.
- `frontend/apps/tenant-admin/`: tenant staff operations console. Owns its admin navigation, role-aware pages and tests.
- `frontend/apps/platform-console/`: SaaS operator console for tenant onboarding, tenant lifecycle and platform metadata.
- `frontend/packages/ui/`: brand-neutral design primitives only.
- `frontend/packages/design-tokens/`: validated tenant theme schema and token mapping.
- `frontend/packages/api-client/`: generated API clients/contracts; not business logic.

The apps may share primitives and tokens but must not collapse into one giant app with extensive tenant/role conditionals. Each app calls backend APIs; no frontend code connects directly to a database.

## Backend roots

Every directory in `backend/services/` is an independent microservice boundary. When implementation begins, it gets its own package name, dependency manifest and lockfile, configuration, Dockerfile, migrations, tests, API contract, README and build/release command. A shared Python application containing all business modules is not an acceptable substitute.

Recommended internal shape:

```text
service-name/
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── migrations/
├── src/<service_package>/
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

This is a service template, not permission to scaffold every service immediately. The selected service gets executable files only when its implementation task is approved.

## Infrastructure and quality roots

- `infra/local/`: local Docker Compose and configuration for developer dependencies. Separate local profiles are preferred so developers start only what they need.
- `quality/e2e/`: browser-level tests crossing frontend and backend boundaries.
- `quality/visual-regression/`: UX regression checks.
- `quality/security-checks/`: repository-level security checks.
- `backend/tests/`: backend contract, integration, tenant-isolation and security tests.

## Naming

Use neutral names such as `commerce-saas-platform`, `catalogue`, `identity-access`, `tenant-admin`, and `platform-console`. Never use `lifemac` as a module/package/service prefix. Lifemac is a tenant fixture.
