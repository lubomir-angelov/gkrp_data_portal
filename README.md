# gkrp_data_portal
A data portal for entry an analysis for the GKRP project.

# repo skeleton
```
gkrp_data_portal/
  core/        (config, logging, security helpers)
  db/          (engine, session, migrations)
  models/      (SQLAlchemy models)
  schemas/     (Pydantic DTOs)
  auth/        (password hashing, tokens, dependencies)
  routers/     (REST endpoints if needed)
  ui/          (NiceGUI pages: data entry + admin + analytics)
  services/    (query service, reporting/export service)
```

# Local setup with make
One-time setup:

```bash
make initial-setup BACKUP_FILE=/absolute/path/to/Pottery_backup_260118.dump
```

Run the app:

```bash
make run
```

Stop DB:
```bash
make down-db
```

Wipe DB volume (dangerous):
```bash
make reset-db
```