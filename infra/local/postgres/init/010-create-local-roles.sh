#!/usr/bin/env bash
set -euo pipefail

: "${PLATFORM_CONTROL_RUNTIME_PASSWORD:?Missing runtime password}"
: "${PLATFORM_CONTROL_MIGRATOR_PASSWORD:?Missing migrator password}"
: "${PLATFORM_CONTROL_WORKER_PASSWORD:?Missing worker password}"
: "${TENANT_DATABASE_PROVISIONER_PASSWORD:?Missing provisioner password}"

# psql reads secret values from the process environment. They are not echoed.
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 <<'SQL'
\getenv runtime_password PLATFORM_CONTROL_RUNTIME_PASSWORD
\getenv migrator_password PLATFORM_CONTROL_MIGRATOR_PASSWORD
\getenv worker_password PLATFORM_CONTROL_WORKER_PASSWORD
\getenv provisioner_password TENANT_DATABASE_PROVISIONER_PASSWORD

CREATE ROLE platform_control_runtime LOGIN PASSWORD :'runtime_password' CONNECTION LIMIT 20;
CREATE ROLE platform_control_migrator LOGIN PASSWORD :'migrator_password' CONNECTION LIMIT 5;
CREATE ROLE platform_control_worker LOGIN PASSWORD :'worker_password' CONNECTION LIMIT 5;
CREATE ROLE tenant_database_provisioner LOGIN PASSWORD :'provisioner_password' CREATEDB CREATEROLE CONNECTION LIMIT 2;

ALTER DATABASE platform_control OWNER TO platform_control_migrator;
REVOKE ALL ON DATABASE platform_control FROM PUBLIC;
REVOKE CONNECT, TEMPORARY ON DATABASE platform_control FROM PUBLIC;
GRANT CONNECT ON DATABASE platform_control TO platform_control_runtime;
GRANT CONNECT ON DATABASE platform_control TO platform_control_migrator;
GRANT CONNECT ON DATABASE platform_control TO platform_control_worker;

\connect platform_control
ALTER SCHEMA public OWNER TO platform_control_migrator;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO platform_control_runtime;
GRANT USAGE ON SCHEMA public TO platform_control_worker;

ALTER DEFAULT PRIVILEGES FOR ROLE platform_control_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO platform_control_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE platform_control_migrator IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO platform_control_runtime;

-- Worker table access is intentionally NOT granted here. The reviewed
-- Platform Control Plane migration grants only the required provisioning-job
-- table permissions. The worker receives no general schema DDL privileges.
SQL
