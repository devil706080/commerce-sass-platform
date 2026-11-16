# Version baseline sources

Versions are a checked starting baseline as of 16 November 2026. Review security advisories and compatibility again before implementation and pin image digests/lockfiles where appropriate.

- Node.js 26 Active LTS: https://nodejs.org/en/about/previous-releases
- Python 3.14.10 release: https://www.python.org/downloads/release/python-31410/
- PostgreSQL 18.7 release and support: https://www.postgresql.org/about/news/postgresql-187-1712-1616-1520-1425-and-19-rc-2-released/ and https://www.postgresql.org/support/versioning/
- PostgreSQL 18 Docker data path (`/var/lib/postgresql/18/docker`, mount `/var/lib/postgresql`): https://github.com/docker-library/docs/blob/master/postgres/README.md
- Redis 8.10.3 release index: https://download.redis.io/releases/
- Mailpit 1.33.1 container: https://github.com/axllent/mailpit/pkgs/container/mailpit
- RabbitMQ 4.4.0 release information: https://www.rabbitmq.com/release-information
- pnpm 12.19.0: https://pnpm.io/blog/releases/12.19.0

The repository pins the local dependency images used in Compose. The frontend and service package dependencies should be selected and locked at the first scaffold; do not pre-generate arbitrary package manifests for services that have not yet been approved.
