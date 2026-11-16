# Local infrastructure

Phase 1A default profile: PostgreSQL 18.7, Redis 8.10.3 and Mailpit 1.33.1. Start only the dependencies needed for the current task. RabbitMQ is an optional `messaging` profile; Kafka is deferred until an approved event-streaming ADR.

Run `python scripts/bootstrap_local.py` from the repository root before invoking Compose. It creates a Git-ignored `.env` and Redis config without printing secrets. See `docs/runbooks/LOCAL_SETUP.md`.
