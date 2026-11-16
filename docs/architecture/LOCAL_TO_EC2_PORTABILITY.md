# Local to EC2 Portability

# Part G — Local to EC2 Portability

# Local to EC2 portability principles

This document is a portability checklist, not an EC2 deployment plan. No cloud resources are created in Phase 1A/1B.

## Application contract

- Each backend service builds its own immutable OCI image from its own Dockerfile.
- Images contain code and dependencies, never credentials, `.env`, local data or tenant-specific branding.
- Configuration is injected at runtime; local and EC2 settings are separate.
- Services run as non-root where feasible, expose health/readiness, handle SIGTERM, use resource limits and do not depend on local bind mounts.
- No authoritative database or media files live in a container writable layer.

## Single EC2 pilot checklist (future)

- VPC/subnet and security groups restrict inbound ports; app/data ports are not public.
- Use SSM Session Manager where possible rather than opening SSH to the internet; enforce IMDSv2 and least-privilege instance role.
- TLS terminates at reviewed reverse proxy/ingress; use secure cookie and trusted-host settings.
- PostgreSQL uses durable encrypted storage, automated backups and tested point-in-time restore; define separate data volume lifecycle and disk alerts.
- Media uses durable object storage and tenant-scoped access, not container local disk.
- Secrets are retrieved through production secret manager/instance IAM; no `.env` copied from developer machine.
- Logs/metrics/traces aggregated; dashboards/alerts for app health, DB saturation, disk, queue backlog, webhook failures, backups and certificate expiry.
- Deploy/rollback procedure, image pinning, migration sequencing and incident runbooks are tested.

## Availability warning

One EC2 instance running Compose can be a pilot/small deployment. It has a single host failure domain and may require downtime for host patching/reboot. It is not HA. Multi-AZ DB, load-balanced app instances, automated failover and regional DR require a separate architecture, budget and operations owner. Choose RPO/RTO and expected traffic before designing production.

---
