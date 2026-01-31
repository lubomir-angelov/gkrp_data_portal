SHELL := /bin/bash

ENV_FILE := .env
COMPOSE := docker compose --env-file $(ENV_FILE) -f docker-compose.yml
PYTHON ?= python

# ---- Defaults (can be overridden via: make run POSTGRES_PASSWORD=... etc.) ----
POSTGRES_USER      ?= postgres
POSTGRES_PASSWORD  ?= postgres
PG_HOST_PORT       ?= 5433
APP_DB             ?= app_db
PG_CONTAINER       ?= gkrp-pg
DUMP_IN_CONTAINER  ?= /tmp/Pottery_backup_260118.dump

# Optional; if empty we can derive it from the above in configure-env
DATABASE_URL       ?=
STORAGE_SECRET     ?=
BACKUP_FILE        ?=

.DEFAULT_GOAL := help

.PHONY: help configure-env show-env up-db down-db reset-db wait-db copy-backup restore-app-db initial-setup run

help:
	@echo "Targets:"
	@echo "  make install-app"
	@echo "      - installs the gkrp_data_portal package into the current python environment"
	@echo "  make show-env"
	@echo "      - shows the contents of $(ENV_FILE) with secrets redacted"
	@echo "  make initial-setup BACKUP_FILE=/path/to/backup.dump"
	@echo "      - configure env, start postgres, copy backup into container, restore+stamp+upgrade"
	@echo "  make run"
	@echo "      - runs the app via python -m gkrp_data_portal (uses $(ENV_FILE))"
	@echo "  make up-db / make down-db"
	@echo "      - start/stop postgres only"
	@echo "  make reset-db"
	@echo "      - stops postgres and deletes the docker volume (DANGEROUS; wipes db)"
	@echo "  make restore-app-db BACKUP_FILE=/path/to/backup.dump"
	@echo "      - copy backup + run create_app_db_from_restore_and_populate.sh"
	@echo ""
	@echo "Notes:"
	@echo "  - $(ENV_FILE) is the source of truth for DATABASE_URL/STORAGE_SECRET/POSTGRES_PASSWORD"
	@echo "  - BACKUP_FILE should be a local path to a pg_dump custom file (.dump/.backup)."
	@echo "  - Host Postgres port defaults to 5433 (override via PG_HOST_PORT=xxxx)."

install-app:
	@set -euo pipefail; \
	$(PYTHON) -m pip install --upgrade pip; \
	$(PYTHON) -m pip install -e ./gkrp_data_portal

show-env:
	@set -euo pipefail; \
	if [ ! -f "$(ENV_FILE)" ]; then echo "$(ENV_FILE) not found. Create make file from template before proceeding."; exit 1; fi; \
	echo "---- $(ENV_FILE) (secrets redacted) ----"; \
	sed -E 's/^(STORAGE_SECRET|POSTGRES_PASSWORD)=.*/\1=<redacted>/' "$(ENV_FILE)"

up-db:
	@set -euo pipefail; \
	$(COMPOSE) up -d db

down-db:
	@set -euo pipefail; \
	$(COMPOSE) down

reset-db:
	@set -euo pipefail; \
	echo "This will delete the postgres volume (all DB data)."; \
	$(COMPOSE) down -v

wait-db:
	@set -euo pipefail; \
	set -a; source "$(ENV_FILE)"; set +a; \
	echo "Waiting for Postgres in container $$PG_CONTAINER ..."; \
	for i in $$(seq 1 60); do \
	  if docker exec -e PGPASSWORD="$$POSTGRES_PASSWORD" "$$PG_CONTAINER" pg_isready -U "$$POSTGRES_USER" -d postgres >/dev/null 2>&1; then \
	    echo "Postgres is ready."; \
	    exit 0; \
	  fi; \
	  sleep 1; \
	done; \
	echo "Postgres did not become ready in time."; \
	exit 1

copy-backup: up-db wait-db
	@set -euo pipefail; \
	set -a; source "$(ENV_FILE)"; set +a; \
	if [ -z "$$BACKUP_FILE" ]; then \
	  echo "BACKUP_FILE is required. Example: make initial-setup BACKUP_FILE=/path/to/Pottery_backup_260118.dump"; \
	  exit 1; \
	fi; \
	if [ ! -f "$$BACKUP_FILE" ]; then \
	  echo "BACKUP_FILE not found on host: $$BACKUP_FILE"; \
	  exit 1; \
	fi; \
	echo "Copying backup into container $$PG_CONTAINER: $$BACKUP_FILE -> $$DUMP_IN_CONTAINER"; \
	docker cp "$$BACKUP_FILE" "$$PG_CONTAINER:$$DUMP_IN_CONTAINER"

restore-app-db: copy-backup
	@set -euo pipefail; \
	set -a; source "$(ENV_FILE)"; set +a; \
	echo "Running restore script with env from $(ENV_FILE)"; \
	bash ./create_app_db_from_restore_and_populate.sh

initial-setup: restore-app-db
	@echo "Initial setup complete."
	@echo "Next:"
	@echo "  make run"

run:
	@set -euo pipefail; \
	set -a; source "$(ENV_FILE)"; set +a; \
	export PYTHONPATH="$$(pwd)/gkrp_data_portal/src:$${PYTHONPATH:-}"; \
	echo "Starting app with DATABASE_URL=$$DATABASE_URL"; \
	$(PYTHON) -m gkrp_data_portal.main
