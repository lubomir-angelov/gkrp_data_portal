# Migration plan (concrete steps)
## Phase 0 — Freeze the source of truth

Tag the current ceramics repo version you consider authoritative.

Confirm you will accept:

fixing the ceramics serialization bugs (they exist)

normalizing date types (recommended) or staying literal

## Phase 1 — New repo skeleton (FastAPI + NiceGUI + Postgres)

Create new repo structure:

app/
  core/        (config, logging, security helpers)
  db/          (engine, session, migrations)
  models/      (SQLAlchemy models)
  schemas/     (Pydantic DTOs)
  auth/        (password hashing, tokens, dependencies)
  routers/     (REST endpoints if needed)
  ui/          (NiceGUI pages: data entry + admin + analytics)
  services/    (query service, reporting/export service)


Configure Postgres connection and session management.

## Phase 2 — Implement models and migrations

Translate ceramics models to SQLAlchemy 2.0 style (or keep classical; both are fine).

Create Alembic migrations:

Base schema

Add auth extensions (role, is_active, invitation fields)

Add image_url to fragments

Add tblfinds

Add indexes for performance:

tblfragments.locationid

tblornaments.fragmentid

tbllayers.layerid

frequent filter columns (e.g., recordenteredon, site/sector/square)

## Phase 3 — Port data-entry UI pages (parity first, polish later)

For each ceramics page:

Implement list page (table + search)

Implement create/edit dialog with the same fields

Preserve the ceramics workflow logic:

where ceramics inferred locationid implicitly, decide explicitly:

either replicate inference (fast parity)

or require explicit selection (better integrity)

I recommend: replicate inference initially for parity, then improve.

## Phase 4 — Add admin + invitation flow

Add admin role checks in a dependency:

Depends(require_admin)

Add admin page:

create invite

list users

activate/disable users

Implement email sending via SMTP.

Replace public registration page with “request access” or remove it entirely.

## Phase 5 — Build the analytics page

Layout: left (columns), center (chart), bottom (table), right (images)

Implement Filter #1 and #2 as selectable queries

Add user-driven filtering & column toggles

Add chart export endpoints (png/jpg/pdf)

Add finds support and tie it into the query selector

## Phase 6 — Data migration

Depends on current production DB:

If ceramics already runs on Postgres: easiest.

If not: write a one-off migration script.

Steps:

Bring up new Postgres schema via migrations.

Extract data from old DB (SQLAlchemy engine to old source).

Insert into new DB in correct order:

layers → fragments → ornaments/includes/pok → finds (if any)

Validate:

row counts per table

random sample row comparison

join integrity checks

## Phase 7 — Deploy with HTTPS

Docker compose:

db (postgres)

app (fastapi+nicegui)

proxy (caddy)

Set environment variables:

DB URL

SMTP

SECRET KEY

external base URL for invite links

Use Caddy for TLS.

## 8) “Fastest build” ordering (what to do first)

If your goal is “usable quickly”, this ordering minimizes risk:

Database + models + migrations (foundation)

Login + admin invite (so you can control access)

Layers + Fragments pages (core workflow)

Ornaments + Includes + POK pages

Analytics page with Filter #1 + table + basic chart

Add: column checkbox panel, images panel, export (png/pdf), finds table


## Required pages (from source of truth)
- Required data entry pages (keep as-is functionally)
- Layers list + create/edit
- Layer includes list + create/edit
- Fragments list + create/edit
- Ornaments list + create/edit
- POK list + create/edit
- Login page (replace)
- Register page (replace with invite flow)