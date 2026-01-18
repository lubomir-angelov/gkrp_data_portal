#!/bin/bash

# 1) create DB
docker exec -e PGPASSWORD=postgres gkrp-pg psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS app_db;"
docker exec -e PGPASSWORD=postgres gkrp-pg psql -U postgres -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE app_db;"

# 2) restore dump (custom format assumed)
docker exec -e PGPASSWORD=postgres gkrp-pg pg_restore \
  -U postgres -d app_db \
  --no-owner --no-privileges \
  ~/tmp/Pottery_backup_260118.dump

# 3) stamp baseline (so Alembic won't try to recreate the restored schema)
export DATABASE_URL="postgresql+psycopg://postgres:postgres@127.0.0.1:5433/app_db"
alembic stamp 0001_base_schema

# 4) apply your app migrations (auth extensions, image_url, finds, indexes)
alembic upgrade head
