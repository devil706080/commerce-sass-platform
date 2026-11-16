# Codex Task: Phase 1A Local Foundation Verification

# Codex task - Phase 1A local foundation verification

You are working in the generic Commerce SaaS Platform monorepo. Read root `AGENTS.md`, `README.md`, `docs/architecture/PHASE_0_ARCHITECTURE_BASELINE.md` and `docs/architecture/PHASE_1_LOCAL_FOUNDATION.md` first.

## Scope

Verify the existing local developer foundation on the user's machine. The repository already contains:
- `infra/local/compose.yaml`
- `infra/local/postgres/init/010-create-local-roles.sh`
- `scripts/bootstrap_local.py`
- `.env.example` and `.gitignore`

Do not redesign the stack or generate any application/service code. Do not install software or make network/cloud changes without the user's explicit consent. Do not print local `.env` secrets.

## Steps

1. Inspect the files and explain the Compose topology and privilege boundaries.
2. Check whether Python, Docker Engine and Compose v2 are available. If Docker is unavailable, report the exact blocker and stop; do not claim the containers are running.
3. If `.env` does not exist, run `python scripts/bootstrap_local.py`. If it exists, do not overwrite it.
4. Run `git check-ignore .env infra/local/secrets/redis.conf` and confirm `.env` and `infra/local/secrets/redis.conf` are ignored. Never display contents.
5. Run `docker compose -f infra/local/compose.yaml config --quiet`.
6. With the user's authorization to run local containers, start only `postgres redis mailpit`.
7. Inspect container health, PostgreSQL roles and local-only port bindings. Do not use the bootstrap/provisioner identity as an application user.
8. Update `docs/runbooks/LOCAL_SETUP.md` only with actual commands/results. Never invent success.

## Forbidden

- Do not create any microservice code, migrations or frontend app.
- Do not start RabbitMQ or Kafka unless separately requested and the reason is documented.
- Do not run `docker compose down -v`.
- Do not reset the local database, rotate secrets or overwrite `.env`.
- Do not use live payment, external SMS/email or public network integrations.

## Completion report

State exact tool versions, files reviewed, commands run, actual results, health status, warnings, what the user must do next, and whether Phase 1A exit criteria are all verified. Stop after Phase 1A. Human approval is required before Phase 1B.

---
