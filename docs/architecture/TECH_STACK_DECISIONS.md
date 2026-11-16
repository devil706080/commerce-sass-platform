# Technology Stack Decisions

# Part C — Technology Stack Decisions

# Technology stack decisions

**Reviewed:** 16 November 2026  
**Decision state:** Selected baseline for local development; exact package patches and lockfiles are finalized per service/app at scaffold time.

## Frontend

- Next.js 16.4.6 App Router, React, TypeScript strict (baseline checked 16 November 2026; update to latest supported security patch in the compatible 16.x line).
- Node.js 26 Active LTS (baseline `.node-version`/`.nvmrc`: 26.13.0); update to latest security patch in the 26.x line after compatibility check.
- pnpm 12.19.0 + Turborepo 2.11.11 for the `frontend/` monorepo only; package manager and runtime are pinned in workspace files.
- Tailwind CSS + Radix primitives/shadcn-based components; shared `ui` and `design-tokens` packages.
- Motion for purposeful transitions; respect `prefers-reduced-motion`.
- TanStack Query for client cache/server state where appropriate; React Hook Form + Zod for forms and validation.
- Storybook, Vitest, Testing Library, Playwright and visual regression for quality.

## Backend

- Python 3.14 bug-fix line (baseline `.python-version`: 3.14.10) with FastAPI and Pydantic v2; refresh patch and dependency lock together.
- SQLAlchemy 2 + Psycopg 3; Alembic migrations.
- `uv` per-service dependency management. Each service owns `pyproject.toml`, `uv.lock`, tests, config and Dockerfile.
- Pytest, Ruff, MyPy or Pyright, coverage reporting and contract tests.
- REST/JSON + OpenAPI 3.1 for synchronous APIs; use versioned event schemas for asynchronous events.

## Data and infrastructure

- PostgreSQL 18.7; database-per-tenant-per-service; separate migrator/runtime roles; bounded tenant pool manager.
- Redis 8.10.3 for cache, rate-limit counters and ephemeral state. It is never the source of truth.
- Mailpit 1.33.1 for local email capture.
- RabbitMQ 4.4.0 optional profile for retryable work queues when justified.
- Apache Kafka 4.4.0 is deferred for event streaming/replay use cases, not basic task scheduling.
- Docker Compose v2 for local dependencies only. Service images are built per service later.

## Deliberately not selected yet

- Production PSP provider and merchant-of-record/settlement model.
- Production search engine (PostgreSQL full-text can support an initial catalogue; dedicated search is later).
- Production object storage/CDN provider (use a storage adapter; local filesystem only in dev).
- Production email/SMS/WhatsApp providers.
- Production secrets manager, EC2 deployment topology, CI/CD provider and HA design.

## Versioning policy

Version strings in architecture docs are baseline snapshots, not permission to ignore patches. Before scaffolding a service/app, check compatibility against official release notes, choose supported stable versions, pin exact direct/transitive dependencies with lockfiles, pin image tags (prefer digest in production), and document the chosen versions. Do not use `latest`, alpha or preview runtimes for production.

See `VERSION_SOURCES.md` for the official version references and PostgreSQL 18 volume-path note.

---
