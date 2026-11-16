#!/usr/bin/env python3
"""Create local-only secrets for the Compose development dependencies.

The script never prints generated secrets and refuses to overwrite an existing
.env or Redis configuration. Run it from any working directory inside the repo.
"""
from __future__ import annotations

import secrets
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
SECRETS_DIR = ROOT / "infra" / "local" / "secrets"
REDIS_CONFIG = SECRETS_DIR / "redis.conf"


def secret() -> str:
    return secrets.token_hex(32)


def main() -> int:
    if ENV_FILE.exists():
        # Recover safely from an interrupted first run without rotating or
        # overwriting the existing .env credentials.
        if REDIS_CONFIG.exists():
            print("Local .env and Redis config already exist; no files were changed.")
            return 0
        parsed: dict[str, str] = {}
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            parsed[key.strip()] = value.strip()
        redis_password = parsed.get("REDIS_PASSWORD", "")
        if not re.fullmatch(r"[0-9a-f]{64}", redis_password):
            print("Existing .env has no valid generated REDIS_PASSWORD; refusing to guess or rotate it.", file=sys.stderr)
            return 2
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        redis_text = (
            "# Generated locally; mounted read-only by Docker Compose.\n"
            f'requirepass "{redis_password}"\n'
            "appendonly yes\nappendfsync everysec\nmaxmemory 256mb\n"
            "maxmemory-policy allkeys-lru\nprotected-mode yes\nbind 0.0.0.0\nport 6379\n"
        )
        try:
            with REDIS_CONFIG.open("x", encoding="utf-8", newline="\n") as f:
                f.write(redis_text)
            try:
                REDIS_CONFIG.chmod(0o600)
            except OSError:
                pass
        except FileExistsError:
            print("Redis config was created concurrently; no existing file was overwritten.")
            return 0
        print("Recovered the missing Redis config from the existing local .env; secrets were not displayed.")
        return 0
    if REDIS_CONFIG.exists():
        print("Redis config already exists but .env does not. Refusing to overwrite either file.", file=sys.stderr)
        return 2

    values = {
        "POSTGRES_HOST_PORT": "5432",
        "REDIS_HOST_PORT": "6379",
        "MAILPIT_SMTP_PORT": "1025",
        "MAILPIT_UI_PORT": "8025",
        "RABBITMQ_AMQP_PORT": "5672",
        "RABBITMQ_MANAGEMENT_PORT": "15672",
        "RABBITMQ_DEFAULT_USER": "local_dev",
        "POSTGRES_BOOTSTRAP_PASSWORD": secret(),
        "PLATFORM_CONTROL_RUNTIME_PASSWORD": secret(),
        "PLATFORM_CONTROL_MIGRATOR_PASSWORD": secret(),
        "PLATFORM_CONTROL_WORKER_PASSWORD": secret(),
        "TENANT_DATABASE_PROVISIONER_PASSWORD": secret(),
        "REDIS_PASSWORD": secret(),
        "RABBITMQ_DEFAULT_PASS": secret(),
    }
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    env_text = "# Generated locally. Never commit, share, or paste this file.\n" + "".join(
        f"{key}={value}\n" for key, value in values.items()
    )
    redis_text = "# Generated locally; mounted read-only by Docker Compose.\n" + (
        f'requirepass "{values["REDIS_PASSWORD"]}"\n'
        "appendonly yes\n"
        "appendfsync everysec\n"
        "maxmemory 256mb\n"
        "maxmemory-policy allkeys-lru\n"
        "protected-mode yes\n"
        "bind 0.0.0.0\n"
        "port 6379\n"
    )
    try:
        # exclusive creation avoids clobbering a concurrently created file
        with ENV_FILE.open("x", encoding="utf-8", newline="\n") as f:
            f.write(env_text)
        with REDIS_CONFIG.open("x", encoding="utf-8", newline="\n") as f:
            f.write(redis_text)
        try:
            ENV_FILE.chmod(0o600)
            REDIS_CONFIG.chmod(0o600)
        except OSError:
            # Windows ACLs, not POSIX mode bits, govern access on Windows.
            pass
    except FileExistsError:
        print("A local secret file appeared during setup. No existing file was overwritten.", file=sys.stderr)
        return 2

    print("Created local-only .env and Redis config. Secret values were not displayed.")
    print("Next: run 'git check-ignore .env infra/local/secrets/redis.conf' before starting Compose.")
    print("Protect this repository directory with your OS account permissions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
