SHELL := /bin/sh
COMPOSE := docker compose -f infra/local/compose.yaml

.PHONY: local-bootstrap local-config local-up local-status local-logs local-down local-down-volumes
local-bootstrap:
	python scripts/bootstrap_local.py

local-config:
	$(COMPOSE) config --quiet

local-up:
	$(COMPOSE) up -d postgres redis mailpit

local-status:
	$(COMPOSE) ps

local-logs:
	$(COMPOSE) logs -f postgres redis mailpit

local-down:
	$(COMPOSE) down

# Destructive: removes all named local data volumes.
local-down-volumes:
	$(COMPOSE) down -v
