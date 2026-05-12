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


## Opencode workflow

Use **one new OpenCode session per phase**. In the TUI, the default keybind for a new session is:

```text
Ctrl+x, then n
```

OpenCode’s docs describe this as the default “leader key” flow: press `ctrl+x`, then press `n` to start a new session. ([OpenCode][1])

## Workflow inside the TUI

### Session 1 — inspect / plan

Start OpenCode:

```bash
cd /path/to/gkrp_data_portal
opencode
```

Switch to the `plan` agent with `Tab`, or mention it explicitly in the prompt. OpenCode docs say `Tab` switches between primary agents, and the `plan` agent is intended for analysis/review without code changes. ([OpenCode][2])

Prompt:

```text
Use the plan agent. Inspect the analytics table and chart pages. Identify the relevant files and propose a minimal implementation plan. Do not edit files.
```

When done, copy/save the useful plan somewhere, for example:

```text
.agent/TASKS.md
```

Then start a new session:

```text
Ctrl+x, then n
```

---

### Session 2 — implement one focused change

In the fresh session, use the implementation agent:

```text
Use the implementator agent. Implement only this change:

<paste one focused item from the plan>

Constraints:
- Touch only the necessary files.
- Preserve existing behavior.
- Run ruff check on touched files if available.
- Do not perform unrelated refactors.
```

After it finishes, inspect manually:

```bash
git status -sb
git diff
```

Then start another new session:

```text
Ctrl+x, then n
```

---

### Session 3 — review diff / fix tests

In the fresh session, ask for review:

```text
Use the reviewer agent. Review the current git diff for correctness, regressions, NiceGUI update issues, SQLAlchemy/query mistakes, and missing tests. Do not edit files yet.
```

Then, if it finds issues:

```text
Use the implementator agent. Fix only the issues found in the review. Do not add unrelated changes.
```

Finally run:

```bash
ruff check .
python -m pytest
git diff
```

## CLI version

You can also do the same with separate `opencode run` calls. Each command is naturally a fresh non-interactive session unless you explicitly continue one.

```bash
opencode run \
  --agent plan \
  "Inspect the analytics table and chart pages. Propose a minimal plan. Do not edit files."
```

Then:

```bash
opencode run \
  --agent implementator \
  "Implement only this focused change: <paste task>. Touch only necessary files."
```

Then:

```bash
opencode run \
  --agent reviewer \
  "Review the current git diff. Do not edit files."
```

## Practical recommendation

For your `gkrp_data_portal` work, use this pattern:

```text
Ctrl+x n  -> Plan task
Ctrl+x n  -> Implement one change
Ctrl+x n  -> Review diff
Ctrl+x n  -> Fix review/test failures
```

Closing and reopening the terminal is not the best reset mechanism because OpenCode can continue or restore previous sessions. Use **`Ctrl+x` then `n`** for an intentional fresh session.

[1]: https://opencode.ai/docs/keybinds/?utm_source=chatgpt.com "Keybinds"
[2]: https://opencode.ai/docs/agents/?utm_source=chatgpt.com "Agents"
