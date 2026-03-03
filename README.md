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

4) Configure your local env
Provide your own secrets/password explicitly
```bash
# copy the template and then add your values
cp .env.tempalte .env
```

Spin up the database from scratch
```bash
make up-db
```

Single-command bootstrap:
```bash
make initial-setup BACKUP_FILE=/abs/path/to/Pottery_backup_260118.dump
make run
```

# Expose to external world
```bash
# this is done on the windows host via PS as Admin!
(base) PS C:\WINDOWS\system32> $wslIp = (wsl hostname -I).Trim().Split(' ')[0]
(base) PS C:\WINDOWS\system32> netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0

(base) PS C:\WINDOWS\system32> netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$wslIp

(base) PS C:\WINDOWS\system32> netsh interface portproxy show all

Listen on ipv4:             Connect to ipv4:

Address         Port        Address         Port
--------------- ----------  --------------- ----------
0.0.0.0         8080        172.20.27.225   8080

(base) PS C:\WINDOWS\system32>
```