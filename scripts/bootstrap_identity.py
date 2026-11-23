#!/usr/bin/env python3
"""Append missing local Keycloak credentials to the ignored root .env."""

from __future__ import annotations

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"


def main() -> int:
    if not ENV_FILE.exists():
        raise SystemExit("Run scripts/bootstrap_local.py first")
    existing = ENV_FILE.read_text(encoding="utf-8")
    keys = {line.split("=", 1)[0].strip() for line in existing.splitlines() if "=" in line}
    values = {
        "KC_BOOTSTRAP_ADMIN_USERNAME": "local-admin",
        "KC_BOOTSTRAP_ADMIN_PASSWORD": secrets.token_urlsafe(32),
        "LOCAL_OPERATOR_EMAIL": "operator@local.test",
        "LOCAL_OPERATOR_PASSWORD": secrets.token_urlsafe(24),
        "TENANT_CONTEXT_BROKER_TOKEN": secrets.token_urlsafe(48),
        "TENANT_CONTEXT_SIGNING_SECRET": secrets.token_urlsafe(64),
        "TENANT_ADMIN_ORIGIN_TEMPLATE": "http://{hostname}:3001",
    }
    missing = [(key, value) for key, value in values.items() if key not in keys]
    if not missing:
        print("Local identity credentials already exist; no files were changed.")
        return 0
    with ENV_FILE.open("a", encoding="utf-8", newline="\n") as file:
        if existing and not existing.endswith("\n"):
            file.write("\n")
        file.write("# Generated local Keycloak identities. Never commit or share.\n")
        for key, value in missing:
            file.write(f"{key}={value}\n")
    print("Added missing local identity credentials to ignored .env; values were not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
