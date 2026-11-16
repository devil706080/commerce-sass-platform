# Service change log

## Platform Control Plane, Increment A

- `pyproject.toml`, `uv.lock`: independent locked dependencies and quality tools.
- `Dockerfile`, `.dockerignore`, `.gitignore`: non-root image and local build/tool exclusions.
- `alembic.ini`, `migrations/env.py`: separate migrator identity and migration environment; no revision or tenant tables.
- `src/platform_control_plane/main.py`: application lifecycle, routing, safe errors and request correlation.
- `core/config.py`, `core/logging.py`: validated database settings and structured safe event logs.
- `database/engine.py`, `database/session.py`, `dependencies/database.py`: bounded pool and request session lifecycle.
- `api/routes/health.py`, `api/routes/readiness.py`, `schemas/health.py`: health and readiness contracts.
- `tests/unit/test_foundation.py`, `tests/integration/test_database.py`: configuration, failure, PostgreSQL identity, DDL denial and session checks.
- `README.md`: local operation and boundaries.
- `infra/local/compose.yaml`: opt-in API profile with runtime credential only, localhost port and PostgreSQL health dependency.
- `docs/progress/IMPLEMENTATION_TRACKER.md`, `SERVICE_CHANGELOG.md`, `TEST_RESULTS.md`: review tracking and observed results.
