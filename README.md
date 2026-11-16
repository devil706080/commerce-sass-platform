# Commerce SaaS Platform

A generic white-label, multi-tenant commerce SaaS platform. Lifemac Pharma is tenant one, not the platform identity. The repository is a monorepo with separate frontend and backend workspaces; each backend service has independent dependencies, data ownership, migrations, tests and a Docker build/release boundary.

## Start here

1. Read `AGENTS.md`.
2. Read `docs/product/PRD.md`.
3. Read `docs/architecture/PHASE_0_1_DELIVERY_BLUEPRINT.md` (or the split Phase 0/Phase 1 docs).
4. If the extracted folder has no `.git` directory, run `git init` once. Then complete the **Phase 1A local developer foundation** using `docs/runbooks/LOCAL_SETUP.md`. This starts only PostgreSQL, Redis and Mailpit.
5. Ask Codex to run `docs/agent-prompts/PHASE_1A_LOCAL_FOUNDATION.md` as a verification-only task.
6. After you review the real results and approve, use `docs/agent-prompts/PHASE_1B_PLATFORM_CONTROL_PLANE.md` to implement only the Platform Control Plane.

Do not let Codex generate all services or all frontend applications at once. Phase 0's technical baseline is prepared; human sign-off and unresolved business/compliance decisions remain open.

## Repository layout

```text
frontend/                 # Storefront, tenant-admin, platform-console and UI-only packages
backend/                  # Independent FastAPI microservices, contracts and tests
infra/local/              # Docker Compose dependencies for local development
docs/                     # PRD, architecture, ADRs, runbooks and Codex prompts
quality/                  # Cross-app E2E, visual and security checks
scripts/                  # Repository-local developer helpers
```

## Local environment scope

Default Compose services: PostgreSQL 18.7, Redis 8.10.3 and Mailpit 1.33.1. RabbitMQ 4.4.0 is optional under the `messaging` profile. Kafka is deferred until a specific event-streaming use case is approved. No application microservice, frontend, public ingress, cloud resource or AI workload is started by the default local setup.

## Key architecture rules

- Tenant business data: database-per-tenant-per-service; provision only enabled tenant/service pairs.
- Control-plane database: platform metadata only; no customer, catalogue, order, inventory or payment source-of-truth records.
- A service can access only its own service databases. Never query another service's database.
- PostgreSQL `PUBLIC` must not retain `CONNECT` or `TEMPORARY` privileges on tenant databases.
- Browser-supplied tenant IDs are not trusted for routing or authorization.
- Payment collection is PSP-hosted/tokenized. PAN/CVV never enter the application; masking is display-only.
- Local Docker Compose is a development dependency stack. One EC2 host later is a pilot, not HA.

## Useful commands (PowerShell)

```powershell
python .\scripts\bootstrap_local.py
git check-ignore .env
docker compose --env-file -f .\infra\local\compose.yaml config --quiet
docker compose --env-file -f .\infra\local\compose.yaml up -d postgres redis mailpit
docker compose --env-file -f .\infra\local\compose.yaml ps
```

Read the runbook before running commands. Do not run `docker compose down -v` unless you intentionally want to delete all local database/cache data.
