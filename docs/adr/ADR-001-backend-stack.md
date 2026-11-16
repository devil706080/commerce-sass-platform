# ADR-001: Backend stack

- Status: Proposed — human review required
- Decision: Python 3.14.x + FastAPI + Pydantic v2 + SQLAlchemy 2 + Psycopg 3 + Alembic; each service owns its `pyproject.toml` and `uv.lock`.
- Rationale: Strong fit for API services and later Python RAG/agent workloads; mature validation and migration ecosystem.
- Consequences: Keep service dependencies isolated; pin exact versions/lockfiles per service; verify dependency compatibility before scaffold.
- Revisit if: load profile, team ownership or dependency support materially changes.
