# Test results

2026-11-16, Platform Control Plane Increment A:

- `uv lock --check`: passed, 38 dependencies resolved.
- `uv run ruff check src tests migrations`: passed.
- `uv run ruff format --check src tests migrations`: passed.
- `uv run mypy src`: passed, 10 source files.
- `uv run pytest tests/unit -q`: 6 passed; FastAPI/Starlette emitted an httpx deprecation warning.
- Initial `RUN_DB_INTEGRATION=1 uv run pytest tests/integration -q`: 2 passed against local PostgreSQL, same warning. Runtime CREATE TABLE was denied.
- After adding a migration-history privilege assertion, `uv run pytest -q` with integration enabled: 7 passed, 1 failed. Runtime has UPDATE on `public.alembic_version` due to pre-existing migrator default table grants. This is an unresolved security issue; permissions were not modified.
- `uv run alembic upgrade head`: exited successfully with migrator credentials and no revision scripts. It created the migrator-owned `public.alembic_version` table.
- Host Uvicorn smoke test on loopback port 18089: `/health` and `/ready` both returned `ok`; process stopped afterward.
- Updated Compose configuration validation with `--env-file .env` and `--profile platform-control`: passed.
- `docker compose --env-file .env -f infra/local/compose.yaml --profile platform-control up -d --build platform-control`: image built and container started. Compose reports healthy and loopback port 8000; HTTP `/health` and `/ready` returned `ok`.

No vulnerability scan, empty-database migration test, or full privilege/security audit has been run.
