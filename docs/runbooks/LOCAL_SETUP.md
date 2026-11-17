# Local Setup Runbook

# Part H — Local Setup Runbook

# Local setup runbook

The canonical setup steps, role boundaries and destructive commands are in `docs/architecture/PHASE_1_LOCAL_FOUNDATION.md`.

## Quick start (PowerShell)

If this folder came from a ZIP and is not yet a Git repository, run `git init` once first. Do not run it again inside an existing repository.

```powershell
python .\scripts\bootstrap_local.py
git check-ignore .env infra/local/secrets/redis.conf
docker compose -f .\infra\local\compose.yaml config --quiet
docker compose -f .\infra\local\compose.yaml up -d postgres redis mailpit
docker compose -f .\infra\local\compose.yaml ps
```

Open Mailpit at `http://127.0.0.1:8025`. PostgreSQL is `127.0.0.1:5432` and Redis is `127.0.0.1:6379`.

## Optional local operator console

After the Phase 1B database migrations have been approved and applied, generate only missing local identity values and start the selected profiles:

```powershell
python .\scripts\bootstrap_identity.py
docker compose --env-file .env -f .\infra\local\compose.yaml --profile identity --profile platform-control --profile platform-console up -d --build
```

Open `http://localhost:3000` and use `LOCAL_OPERATOR_EMAIL` / `LOCAL_OPERATOR_PASSWORD` from the ignored `.env`. Do not paste them into source code, Postman collections, chat or logs. Keycloak runs at `http://localhost:8080` in development mode and the API at `http://localhost:8000`.

No separate migration command is required for ordinary restarts after Alembic reports revision `003_audit_actor`. Never run migrations with the API runtime or bootstrap administrator identity.

## Troubleshooting checklist

1. `docker version` fails: start Docker Desktop and wait until the Linux engine is running.
2. `docker compose config` fails with a missing variable: run `python scripts/bootstrap_local.py` and confirm `.env` exists in repository root.
3. Port is already allocated: change the corresponding host port in ignored `.env`, then recreate that service.
4. PostgreSQL init role script did not rerun: init scripts execute only on an empty data volume; use a reviewed migration or deliberately reset disposable data with `docker compose ... down -v`.
5. Mailpit is empty: configure the application SMTP host as `mailpit`, port `1025` from a container; from host use `127.0.0.1:1025`.
6. Never fix a credential error by using `local_bootstrap_admin` in an application. Identify the intended runtime/migrator/worker/provisioner identity instead.

## Verification record

Record date, Docker/Compose versions, command output, role checks and any port changes here. Do not record passwords or tokens.

| Check | Result | Date / notes |
|---|---|---|
| Docker Engine | Running; Compose reports services healthy | 2026-11-16 |
| Compose config | Passed using `--env-file .env` | 2026-11-16 |
| PostgreSQL healthy | PostgreSQL 18.7; socket connection to `platform_control` succeeded | 2026-11-16 |
| PostgreSQL roles | All four intended roles exist and authenticate over TCP; database and public schema owned by migrator | 2026-11-16 |
| PostgreSQL privileges | Runtime, migrator and worker can connect; runtime has schema USAGE but not CREATE; PUBLIC has neither database CONNECT nor TEMPORARY | 2026-11-16 |
| Redis healthy | Authenticated PING returned PONG | 2026-11-16 |
| Mailpit UI | HTTP 200 on localhost:8025; no external email sent | 2026-11-16 |
| Port bindings | PostgreSQL 5432, Redis 6379, Mailpit 1025 and 8025 bound to 127.0.0.1 | 2026-11-16 |
| Git ignores secrets | `.env` and `infra/local/secrets/redis.conf` ignored | 2026-11-16 |
| Local operator authentication | Keycloak Authorization Code + PKCE, issuer/audience/role checks and authorized tenant API passed | 2026-11-17 |
| Platform console | Production image built; localhost:3000 returned HTTP 200 | 2026-11-17 |
| Provisioning migration | Alembic `006_provisioning_jobs` applied by `platform_control_migrator` | 2026-11-17 |
| Lifemac fixture databases | Catalogue and Inventory migrations reached `MIGRATED`/`PASSED`; Lifemac was activated through the authenticated console | 2026-11-17 |
| Tenant/service isolation | Catalogue runtime was denied connection to Inventory; PUBLIC CONNECT and TEMPORARY are revoked | 2026-11-17 |

## Local provisioning worker

The HTTP API never receives worker or database-provisioner credentials. Start the isolated worker with:

```powershell
docker compose --env-file .env -f .\infra\local\compose.yaml --profile provisioning up -d --build platform-provisioner
```

Schema changes remain an explicit operation. Run the reviewed control-plane migrations only through the dedicated migrator service:

```powershell
docker compose --env-file .env -f .\infra\local\compose.yaml --profile migration run --rm --build platform-control-migrate
```

The worker creates infrastructure only. It does not run Catalogue, Inventory, or any other owning-service migration. Local generated service credentials are held in the `provisioned_secrets` Docker volume; the control database stores only `local-volume://...` references.

PowerShell sessions with Docker's user installation may need a fresh PATH. Because the Compose file is in `infra/local`, use `docker compose --env-file .env -f .\infra\local\compose.yaml` from the repository root. The control-plane local exit gate is complete; production identity hardening, external domain verification, backups, and monitoring remain future work.

---
