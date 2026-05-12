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

(base) PS C:\WINDOWS\system32> netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=9999 connectaddress=$wslIp

(base) PS C:\WINDOWS\system32> netsh interface portproxy show all

Listen on ipv4:             Connect to ipv4:

Address         Port        Address         Port
--------------- ----------  --------------- ----------
0.0.0.0         8080        172.20.27.225   8080

(base) PS C:\WINDOWS\system32>


netsh advfirewall firewall add rule name="WSL NiceGUI 8080" dir=in action=allow protocol=TCP localport=8080

#And if you’re on Windows 11 / recent WSL, also inspect Hyper-V firewall because Microsoft documents that it can filter WSL traffic by default:

Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}'
Get-NetFirewallHyperVRule -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}'

Then test in this order:

1. Inside WSL:        curl http://127.0.0.1:8080
2. From Windows host: http://localhost:8080
3. From another LAN device: http://<windows-lan-ip>:8080
4. From outside your home network: http://<your-public-static-ip>:8080
```


## Testing opencode setup
```bash
ubuntu@ggbg-pc-rig:~/experiment/gkrp_data_portal$ git status -sb
## feature/opencode_work...origin/feature/opencode_work
ubuntu@ggbg-pc-rig:~/experiment/gkrp_data_portal$ ls -la opencode.json AGENTS.md
-rw-r--r-- 1 ubuntu ubuntu 1917 May 12 07:27 AGENTS.md
-rw-r--r-- 1 ubuntu ubuntu 7480 May 12 08:09 opencode.json
ubuntu@ggbg-pc-rig:~/experiment/gkrp_data_portal$ opencode models llamacpp
llamacpp/Qwen3.6-27B-UD-Q5_K_XL
llamacpp/Qwen3.6-35B-A3B-UD-Q4_K_XL
ubuntu@ggbg-pc-rig:~/experiment/gkrp_data_portal$ opencode run \
  --model llamacpp/Qwen3.6-27B-UD-Q5_K_XL \
  --agent plan \
  "Reply with exactly: opencode-ok"

> plan · Qwen3.6-27B-UD-Q5_K_XL

opencode-ok

ubuntu@ggbg-pc-rig:~/experiment/gkrp_data_portal$ opencode run \
  --agent plan \
  "Inspect this repository. Identify the main Python package, the web UI framework, the database layer, and the likely commands for linting and tests. Do not edit files."
```