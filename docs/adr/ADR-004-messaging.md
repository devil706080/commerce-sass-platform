# ADR-004: Background jobs and event streaming

- Status: Proposed — human review required
- Decision: No broker in default Phase 1A profile. Introduce RabbitMQ when a concrete background-job consumer, retry and dead-letter requirement exists. Defer Kafka until replayable/high-volume event streaming and multiple independent consumers justify its operational cost.
- Reliability: Transactional outbox for events; idempotent consumers; schema/version governance; per-tenant authorization and resource quotas.
