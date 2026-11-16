# Phase 1A Local Developer Foundation

# Part B — Phase 1A Local Developer Foundation

# Phase 1A - Local Developer Foundation

**Status:** Ready for local execution  
**Scope:** Start only shared development dependencies; do not scaffold every app/service.  
**Target OS:** Windows 11 + PowerShell, with equivalent macOS/Linux commands below.

## 1. What Phase 1A provides

This is the small local foundation needed before implementing the Platform Control Plane. The default Docker Compose profile starts only:

| Container | Pinned image baseline | Purpose | Host endpoint |
|---|---|---|---|
| PostgreSQL | `postgres:18.7` | Control-plane DB now; separate tenant/service DBs later | `127.0.0.1:5432` |
| Redis | `redis:8.10.3` | Cache/ephemeral state for future services | `127.0.0.1:6379` |
| Mailpit | `ghcr.io/axllent/mailpit:v1.33.1` | Capture local email/OTP messages | SMTP `127.0.0.1:1025`, UI `http://127.0.0.1:8025` |

RabbitMQ `4.4.0` is available under the optional `messaging` profile when a service actually needs background queues. Kafka is intentionally not included in the default local setup; introduce it only after a separate ADR justifies replayable event streaming. This avoids making every developer run a large event stack before it is needed.

The Compose file runs dependencies only. It does not start fifteen microservices, frontend apps or a gateway. During service work, run the single app on your host during development or use its own Dockerfile after that service is ready.

## 2. Prerequisites

Install once on the development machine:

- Docker Desktop with Docker Compose v2, using Linux containers.
- Git.
- Python 3.14.x (use the latest approved 3.14 patch; baseline checked at 3.14.10).
- Node.js 26.x Active LTS for frontend work (baseline checked at 26.13.0); not required to start the local infrastructure.
- VS Code and Codex.
- `uv` for Python service environments and `pnpm` for frontend work. Install these when the first corresponding service/app is scaffolded; they are not prerequisites for Phase 1A's infrastructure-only start. For Node.js 26, do not assume Corepack is bundled (it stopped shipping with Node.js starting at v25); on Windows use `npm install -g pnpm@12.19.0`, then verify `pnpm --version`.

Do not install PostgreSQL or Redis directly on Windows. Docker Compose owns the local database/cache runtime so that versions match the project and can be reset consistently.

## 3. Windows PowerShell first run

Run commands from the repository root `commerce-saas-platform/`. If the folder came from a ZIP and has no `.git` directory, initialize Git once with `git init`; do not reinitialize an existing repository.

```powershell
# 1. Confirm Docker Engine and Compose are available
docker version
docker compose version

# 2. Create a local-only .env with random credentials (never prints them)
python .\scripts\bootstrap_local.py

# 3. Review that .env is ignored before continuing
git check-ignore .env infra/local/secrets/redis.conf

# 4. Validate the Compose model
docker compose -f .\infra\local\compose.yaml config --quiet

# 5. Start only the required local dependencies
docker compose -f .\infra\local\compose.yaml up -d postgres redis mailpit

# 6. Confirm health/state
docker compose -f .\infra\local\compose.yaml ps
```

Expected local endpoints:

- PostgreSQL: `localhost:5432`, database `platform_control`.
- Redis: `localhost:6379` (password is in the ignored `.env`; do not paste it into chat).
- Mailpit UI: `http://127.0.0.1:8025`; SMTP host from another container: `mailpit`, port `1025`; from host: `127.0.0.1:1025`.

### Verify PostgreSQL roles

```powershell
docker compose -f .\infra\local\compose.yaml exec postgres psql -U local_bootstrap_admin -d platform_control -c "\du"
```

You should see `platform_control_runtime`, `platform_control_migrator`, `platform_control_worker` and `tenant_database_provisioner`. The bootstrap administrator is a local initialization account, not an application user. The API uses only the runtime role. The separate provisioning worker uses the worker role for narrowly granted job-table access and the provisioner role only for database/role creation. Neither worker credential may be injected into the HTTP API process.

To inspect the initial database ACL (no password values are displayed):

```powershell
docker compose -f .\infra\local\compose.yaml exec postgres psql -U local_bootstrap_admin -d platform_control -c "SELECT datname, datacl FROM pg_database WHERE datname = 'platform_control';"
```

The ACL must not grant `CONNECT` to `PUBLIC`; it must explicitly allow the platform migrator, runtime and worker roles. The provisioner must not have `CONNECT` to `platform_control`. Later tenant databases must revoke both `CONNECT` and `TEMPORARY` from `PUBLIC` and grant `CONNECT` only to their owning service's runtime/migrator roles.

To test the runtime connection from a host psql client, read the generated password locally from `.env` and set `PGPASSWORD` only in the current PowerShell process. Do not put it in a command committed to documentation or scripts:

```powershell
$env:PGPASSWORD = '<copy PLATFORM_CONTROL_RUNTIME_PASSWORD from local .env>'
psql -h 127.0.0.1 -p 5432 -U platform_control_runtime -d platform_control -c "select current_user, current_database();"
Remove-Item Env:PGPASSWORD
```

A freshly initialized database has no application tables until the Platform Control Plane migrations are implemented in Phase 1B. A runtime connection is expected to work, but no business API exists yet.

### Optional RabbitMQ profile

Only when an approved service task requires asynchronous jobs:

```powershell
docker compose -f .\infra\local\compose.yaml --profile messaging up -d rabbitmq
```

Management UI: `http://127.0.0.1:15672`. Credentials are in `.env`. Do not create queues or add consumers as part of unrelated service tasks.

## 4. macOS/Linux equivalent

```bash
python3 scripts/bootstrap_local.py
git check-ignore .env infra/local/secrets/redis.conf
docker compose -f infra/local/compose.yaml config --quiet
docker compose -f infra/local/compose.yaml up -d postgres redis mailpit
docker compose -f infra/local/compose.yaml ps
```

## 5. Everyday commands

```powershell
# Status
docker compose -f .\infra\local\compose.yaml ps

# Follow PostgreSQL logs
docker compose -f .\infra\local\compose.yaml logs -f postgres

# Stop containers but preserve data volumes
docker compose -f .\infra\local\compose.yaml down

# Start again without rebuilding data
docker compose -f .\infra\local\compose.yaml up -d postgres redis mailpit

# Remove containers AND all local database/cache/queue data (destructive)
docker compose -f .\infra\local\compose.yaml down -v
```

**Warning:** `down -v` deletes the local PostgreSQL, Redis and RabbitMQ volumes. Do not run it casually. The PostgreSQL initialization script runs only when the data directory is empty. If you change the init script after first startup, it will not rerun on an existing volume; create and apply a reviewed SQL migration or deliberately reset disposable local data.

If a host port is occupied, stop the conflicting process or edit the corresponding host port in `.env` (`POSTGRES_HOST_PORT`, `REDIS_HOST_PORT`, `MAILPIT_SMTP_PORT`, `MAILPIT_UI_PORT`) then run `docker compose ... up -d` again. Do not change the container ports.

## 6. Local credential boundaries

The bootstrap script creates `.env` with random hex secrets and refuses to overwrite an existing file. `.env` is Git-ignored. It is not safe to upload, commit, email or paste into Codex prompts. The script does not print secrets. On Windows, protect the repository folder with the logged-in user's filesystem permissions; on POSIX the file is created with mode `0600`.

PostgreSQL roles:

| Role | Purpose | Allowed in an API process? |
|---|---|---|
| `local_bootstrap_admin` | Initial local database/role setup only; superuser created by official image | **No** |
| `platform_control_migrator` | Apply Control Plane schema migrations | Migration job only |
| `platform_control_runtime` | Runtime CRUD on granted Control Plane schema objects | Yes, Control Plane API only |
| `platform_control_worker` | Narrow provisioning-job table access granted by migrations | **No**, provisioning worker only |
| `tenant_database_provisioner` | Local-only CREATE DATABASE/ROLE for isolated provisioning worker | **No**, provisioning worker only |

In the first initialization script, `platform_control` ownership is transferred to `platform_control_migrator`; runtime and worker receive no DDL privileges. The worker role receives only `CONNECT` initially; the Platform Control Plane migration explicitly grants the minimum provisioning-job schema/table permissions. For each tenant/service DB, the provisioner must revoke `CONNECT` and `TEMPORARY` from `PUBLIC` and grant `CONNECT` only to that DB's service runtime/migrator roles; owner-service migrations set schema/table ACLs. Per-tenant/service DB roles are created by the future isolated provisioning workflow, not by one giant SQL init file. Each owning service, not the Control Plane, applies its own migrations.

## 7. Phase 1A exit criteria

- [ ] Docker Engine and Compose v2 installed and responding.
- [ ] Local `.env` generated and Git-ignored.
- [ ] `docker compose ... config --quiet` passes.
- [ ] PostgreSQL, Redis and Mailpit start and remain healthy.
- [ ] PostgreSQL roles are visible and have the intended distinct privileges.
- [ ] PostgreSQL host port is bound to loopback, not `0.0.0.0`.
- [ ] Mailpit UI loads locally and can receive a test message when an app is later configured.
- [ ] `down` preserves volumes; the destructive `down -v` behavior is understood.
- [ ] No application/service implementation has been generated by Phase 1A.

Record actual outputs in `docs/runbooks/LOCAL_SETUP.md` or a local issue. Do not mark any checklist item complete until it has been run on the developer's machine.

## 8. Phase 1B - Platform Control Plane (next approved coding task)

After Phase 1A is verified, begin **only** `backend/services/platform-control-plane/`.

Scope for the first Control Plane increment:

1. Review/accept ADR-001, ADR-003, ADR-011 and ADR-015.
2. Define tenant registry, tenant domain, lifecycle and provisioning-job domain model.
3. Define OpenAPI contract and error model before implementation.
4. Implement health/readiness endpoints, configuration validation and platform-control database migration baseline.
5. Implement create/list/get/update tenant lifecycle with idempotency and audit metadata.
6. Implement a provisioning state machine and worker boundary, but do not hand CREATE DATABASE/CREATEROLE credentials to the normal API process.
7. Add a local domain resolver adapter for two synthetic tenants; production DNS verification is designed but not publicly activated locally.
8. Prove two tenants receive separate logical DBs for at least the first provisioned service; a second service database should be a fixture to prove the service dimension is part of the database key.
9. Test unknown, unverified, suspended and partially provisioned tenants fail closed.
10. Document recovery, retry, rollback and operator-visible state.

Do not implement Identity, Catalogue, Storefront, Payment, Kafka, AI, EC2 or production DNS flows in this first service task. Do not build a full tenant-facing admin UI before the control-plane API contract is accepted.

### Phase 1B exit gate

Two synthetic tenants are created through the Control Plane; provisioning creates distinct opaque DB names and distinct service credentials; Tenant A's credentials cannot connect to Tenant B's database; the provisioning credential is used only by the isolated worker; suspended/unknown tenants are denied; API contract and migrations are documented; tests and code walkthrough are reviewed; human approval is recorded. Only then may Identity & Access begin.

## 9. Local to EC2 portability checks

The local package is a developer environment, not the EC2 production architecture. Every service task must:

- Read configuration from environment/config providers, never hardcode localhost or credentials.
- Expose health/readiness endpoints and accept graceful termination.
- Build a self-contained, immutable OCI image with pinned dependencies; no local bind mounts in production.
- Persist no authoritative business data in container writable layers.
- Keep secrets outside images and source control.
- Use external database/object-storage/message endpoints supplied by deployment config.
- Document CPU/memory assumptions, ports, startup dependencies and health checks.

Before EC2 production, complete separate decisions for DB hosting/backup, object storage, TLS/ingress, secrets/IAM, network segmentation, logging/monitoring, deployment/rollback, RPO/RTO, patching and disaster recovery. One EC2 host is a pilot deployment, not a high-availability design.

---
