# PROGRESS — Project 1: Sovereign Regulatory AI Assistant

For a new chat: read this whole file first. Continue from **Current position**. Full plan: **Project 1 — Roadmap v3** (Project files, and https://claude.ai/code/artifact/69380837-fa7a-410d-bff3-ced256ff6bf0). Repo: https://github.com/Yazanakkad/sovereign-regulatory-assistant (this file lives in the repo root; the copy in the Claude Project is re-uploaded after each session).

## 1. Current position

| | |
| --- | --- |
| Plan | Roadmap v3 (since 2026-10-24): 52 weeks, business and architecture stages added, three exams interleaved |
| Stage | Stage 1 — Linux and networking (weeks 1–5, 36 h) |
| Last completed | Step 14 — Bash backup script + systemd service and timer (14a–14e; ADR-0011) |
| Next step | Confirm the 02:30 Riyadh scheduled backup ran (`systemctl list-timers regassist-backup.timer --no-pager`; `journalctl -u regassist-backup --since "2026-10-26 23:00 UTC" -o cat --no-pager`), then Step 15 — Networking lab (see section 4) |
| Budget spent | $0 of $20 (OpenAI $0 / 5 · Azure $0 / 10 reserve · contingency $0 / 5) |

## 2. How we work (rules for every chat)

- One step at a time. Every step has exactly: What · Why · Do this · Check · What I should understand · Exam map.
- Keep instructions simple: one action at a time, the machine named for every command (Windows PowerShell, Admin PowerShell, WSL, VM over SSH, or browser), no side notes in the middle of a flow.
- Gates over commands. A stage ends only when its gate is demonstrated.
- When something fails: diagnose → likely cause → smallest diagnostic command → wait for output → fix → re-test. Don't list five fixes at once.
- No silent architecture changes. Explain why, what changes, roadmap impact, then ask for approval.
- Cost: never create a chargeable resource without naming it, checking current pricing, and getting approval. Hard cap $20 total.
- Current facts are looked up (Azure services, models, pricing, regions, exam objectives, software versions) from official sources.
- Commands: prefer one-liners joined with `;` (pastes sometimes lose line breaks); use `&&` when a later command must only run if the earlier one succeeded (commit + push). Server work over SSH, not the Hyper-V console. Repo work in WSL.
- Multi-line files are edited in VS Code (opened from WSL with `code .`); large sets of generated files may come as a downloadable archive, which is read before committing.
- Exam map list: PSPO I · TOGAF EA Foundation · AB-100 · Kubernetes curriculum (reference). Otherwise: "No direct exam mapping — production engineering skill." (AI-103, AZ-104 and Terraform Associate were removed in v3; Terraform stays as a skill.)
- Business stages (1b, 1c, 4c) follow the same step format; their outputs live in `docs/business/` and `docs/architecture/`.
- End of session: the assistant updates this file; commit it in the repo, push, and re-upload it to the Claude Project.

## 3. Environment snapshot (current state)

**Host laptop**

- Windows 11 Pro (build 26200), i7-1355U 10 cores / 12 threads, 40 GB RAM (~27 GB free after reboot), 308 GB free disk
- Hyper-V enabled; WSL 2.6.3 — distros: Ubuntu-24.04 (default), docker-desktop
- Docker Desktop installed (used from Stage 3); no `.wslconfig` yet (memory cap added in Stage 3)
- VS Code with the WSL extension (Microsoft); VS Code Server installed in WSL; Auto Save on
- Windows clock syncs from the employer domain (WAK-AD.WAK.local) and drifts when off the corporate network (189 s fast on 2026-10-26, last sync 2026-10-21) → run `w32tm /resync` (Admin PowerShell) when on the corporate network/VPN. Kerberos tolerates 5 min.

**Dev workstation (WSL Ubuntu 24.04.5)**

- Repo: `~/code/sovereign-regulatory-assistant` (Linux filesystem, not `/mnt/c`)
- uv 0.12.23 in `~/.local/bin`; project Python 3.13.16 (uv-managed); system Python 3.12.3 untouched
- git 2.43.0; identity Yazan Alaqqad / GitHub noreply email; `init.defaultBranch main`; `pull.ff only`
- Dev deps (locked in uv.lock): ruff, mypy, pytest 9.1.1, pre-commit 4.6.2
- pre-commit hooks: pre-commit-hooks v6.0.0, gitleaks v8.30.0, shellcheck-py (pinned by autoupdate), local ruff/mypy via `uv run`
- Repo contents:
  - `src/regassist/` (`__init__.py`, `server.py` stdlib placeholder service)
  - `tests/` (22 tests, incl. `test_backup_script.py` run against temporary directories)
  - `deploy/systemd/` (`regassist-app.service`, `regassist-backup.service`, `regassist-backup.timer`)
  - `deploy/backup/regassist-backup.sh`
  - `docs/adr/` (ADR-0001–0011), `docs/runbooks/backup-restore.md`
- Daily commands: `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy src tests` · `uv run pytest`
- Before `git add`: `uv run ruff check --fix .; uv run ruff format .` (hooks that modify files abort the commit); chain commit and push with `&&`

**GitHub**

- Public repo Yazanakkad/sovereign-regulatory-assistant, branch main tracking origin/main
- WSL key `~/.ssh/id_ed25519_github` (passphrase, comment yazan@wsl-github), fingerprint SHA256:mtuosChtw2cp1lmWq094+5AeRN9+veLQjgv8sy4TpV8, account "Authentication Key" titled wsl-regassist
- Deploy key "regassist-srv01 (read-only)", fingerprint SHA256:IL5YD46CODYOU/dr+38nAiKwPMtgAp/54w+7YtkUTVo (VM only)
- GitHub ED25519 host key verified against docs.github.com: SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU

**VM regassist-srv01**

- Hyper-V Gen2, 2 vCPU, 4 GB fixed RAM, 40 GB VHDX at `C:\VMs\regassist-srv01\`, automatic checkpoints off
- Secure Boot on, template MicrosoftUEFICertificateAuthority; ISO detached, boots from disk
- Hyper-V integration services: Time Synchronization **disabled** (ADR-0010); Guest Service Interface off; KVP "No Contact" (no KVP daemon, harmless)
- Ubuntu Server 26.04.1 LTS, kernel 7.0.0-38-generic, LVM root 37 GB (7 GB used), swap 3.8 GiB
- System Python 3.14.4 (`/usr/bin/python3`; dev uses 3.13 — skew removed by Docker in Stage 3); git 2.53.0
- Tools: tar, gzip, zstd, sha256sum, flock present; strace installed (diagnostics); shellcheck not installed (runs in WSL via pre-commit)
- Fully patched; unattended security upgrades on (apt-daily* timers)
- Time (ADR-0010): chrony 4.8 is the only clock writer, Ubuntu NTS servers, drop-in `/etc/chrony/conf.d/10-regassist-makestep.conf` (`makestep 1 -1`); clock and logs in UTC (Riyadh = UTC+3)
- Journal persistent in /var/log/journal (~21 MB)

**Network**

- VM eth0: DHCP from Default Switch — currently 172.27.56.52/20 (can change; always use the name)
- Name: regassist-srv01.mshome.net (Default Switch DNS) · host side of switch: 172.27.48.1
- VM DNS path: app → 127.0.0.53 (systemd-resolved) → 172.27.48.1 (Windows host) → internet
- WSL → VM works via IPv4 forwarding on vEthernet (WSL (Hyper-V firewall)) + vEthernet (Default Switch); VM sees WSL's own IP (routed, not NATed)

**Access**

- User yazan (groups include sudo, adm; removed from lxd)
- Server host key: ED25519 SHA256:GqrCzbHA3iwDOCyHn8h/dQyEvRePV1k44z8VlGsXs2Q
- Windows client: key `~/.ssh/id_ed25519_regassist` (passphrase, Windows ssh-agent), alias `ssh regassist`
- WSL client: key `~/.ssh/id_ed25519_regassist_wsl` (comment yazan@wsl-regassist), alias `ssh regassist`; `~/.ssh/config` also has the github.com block
- VM deploy key `~/.ssh/id_ed25519_deploy_regassist` (no passphrase, comment regassist-srv01-deploy, read-only to one repo); VM `~/.ssh/config` github.com block (IdentitiesOnly); GitHub ED25519 host key pinned in the VM's known_hosts
- sshd drop-in `/etc/ssh/sshd_config.d/10-hardening.conf`: keys only, no root, AllowUsers yazan, MaxAuthTries 3, no X11

**Service account and layout (ADR-0008)**

- regassist: system user UID 999 / GID 983, shell /usr/sbin/nologin, home /nonexistent, password locked, no sudo, outside sshd AllowUsers
- `/srv/regassist` root:root 0755 · `app/` yazan:regassist 2750 (setgid) · `data/` regassist:regassist 0750 · `/etc/regassist` root:regassist 0750
- yazan login umask is 0002 → anything written into `app/` runs as `(umask 027; …)`; post-deploy check `find /srv/regassist/app -perm -g+w` must print nothing
- Never run Python as yazan inside `app/` (it would write group-writable `__pycache__`)
- `data/demo/` holds two small test files (`note.txt`, `file with space.txt`, owned by regassist) used by the backup drills

**Service regassist-app (ADR-0009)**

- Unit `/etc/systemd/system/regassist-app.service` = root-owned copy of `deploy/systemd/regassist-app.service`; enabled; Type=exec; runs as regassist
- Listens on 127.0.0.1:8000; `GET /health` → `{"status": "ok", "version": "0.0.0+source"}`
- Config `/etc/regassist/regassist.env` (REGASSIST_HOST, REGASSIST_PORT), root:regassist 0640
- Sandbox: exposure 1.1 OK (was 9.2); only `data/` writable; private /tmp, /var/tmp, /dev/shm; no capabilities; localhost-only network
- Restart=on-failure (2 s), no restart on exit 2 (bad config), max 5 starts/60 s; SyslogIdentifier=regassist-app; JSON logs with syslog priority
- Deploy: `(umask 027; git -C /srv/regassist/app pull)`; if the unit changed: `sudo install -m 0644 -o root -g root /srv/regassist/app/deploy/systemd/regassist-app.service /etc/systemd/system/; sudo systemctl daemon-reload; sudo systemctl restart regassist-app`
- Logs: `journalctl -u regassist-app` · `-p err` · `-o cat` · `-b -1` (previous boot) · `--since "15 min ago"`

**Backups (ADR-0011)**

- Script `/usr/local/sbin/regassist-backup` = root-owned 0755 copy of `deploy/backup/regassist-backup.sh`
  - Sources: `srv/regassist/data`, `etc/regassist` (relative to `/`); code is not backed up (git is the source of truth)
  - Flow: config checks → `flock` → temp file in the backup dir → read the whole archive back → SHA-256 file → atomic rename → `sync` → retention
  - Exit codes: 0 ok · 1 failed (tool failures mapped to 1; original code logged as `cause_exit`, with `line` and `command`) · 2 bad configuration · 3 locked
  - Env overrides: `REGASSIST_BACKUP_DIR`, `REGASSIST_BACKUP_KEEP` (default 7), `REGASSIST_BACKUP_SOURCE_ROOT`
  - Logs: logfmt (`event=… key=value`) with syslog priority prefix
- Destination `/var/backups/regassist` root:root 0700; archives `regassist-YYYYMMDDTHHMMSSZ.tar.gz` + `.sha256`, both 0600; `.lock` 0600
- Retention: newest 7 by count, pruned only after a verified success, never the archive just written (clock-jump safe)
- Unit `regassist-backup.service`: Type=oneshot, static (started by the timer), root reduced to `CAP_DAC_READ_SEARCH`, `ProtectSystem=strict` + `ReadWritePaths=/var/backups/regassist`, no network (`PrivateNetwork`, `IPAddressDeny=any`, AF_UNIX only), seccomp `@system-service`, `TimeoutStartSec=30min`, Nice 10 / IO best-effort 7; exposure 1.3 OK
- `RestrictSUIDSGID=` deliberately not set on the backup unit: its seccomp filter answers `openat2()` with ENOSYS and the Ubuntu 26.04 tar uses `openat2()` (compensating controls: ProtectSystem=strict, 0700 root-only destination, NoNewPrivileges)
- Timer `regassist-backup.timer`: `OnCalendar=*-*-* 02:30:00 Asia/Riyadh` (23:30 UTC), `Persistent=true`, enabled
- Deploy: `(umask 027; git -C /srv/regassist/app pull); sudo install -m 0755 -o root -g root /srv/regassist/app/deploy/backup/regassist-backup.sh /usr/local/sbin/regassist-backup`; units: `sudo install -m 0644 -o root -g root /srv/regassist/app/deploy/systemd/regassist-backup.{service,timer} /etc/systemd/system/; sudo systemctl daemon-reload`
- Run now: `sudo systemctl start regassist-backup.service`; health check and restores: `docs/runbooks/backup-restore.md`
- Measured technical RTO: 0.34 s (full `data/` restore, 2026-10-27); RPO up to 24 h
- Current archives: 4 (2026-10-26 20:26, 21:00, 21:04 and the post-drill run)

**Firewall (ufw)**

- Active, starts on boot; default deny incoming / allow outgoing / routed disabled
- 22/tcp LIMIT; logging low → blocked packets: `sudo journalctl -k -g 'UFW BLOCK'`

**Hyper-V checkpoints:** 01-base-install, 02-ssh-hardened, 02-hardened-patched, 03-pre-firewall, 04-firewall, 05-service-account, 06-systemd-service, 07-backup

**Known quirks**

- Hyper-V console can't paste (keyboard layout) → use SSH only
- Pastes may join lines → use the code block copy button / Windows Terminal, or `;` one-liners
- After a reconnect, check the prompt before pasting: `PS C:\…>` = Windows, `yazan@yazan` = WSL, `yazan@regassist-srv01` = VM
- WSL → VM forwarding resets after Windows reboot or WSL restart → re-run (Admin PowerShell): `Set-NetIPInterface -InterfaceAlias "vEthernet (WSL (Hyper-V firewall))","vEthernet (Default Switch)" -AddressFamily IPv4 -Forwarding Enabled` (automation pending — ADR-0005)
- Open VS Code from WSL (`cd ~/code/sovereign-regulatory-assistant; code .`); bottom-left must show WSL: Ubuntu-24.04. "Insert final newline" is enabled in VS Code settings.
- VS Code: create new files with **New File at the repo root and the full path** (e.g. `deploy/backup/x.sh`); right-clicking a compacted `deploy / systemd` row creates the file inside `systemd/`. Auto Save is on because an unsaved edit once dropped out of a commit.
- `pre-commit run --all-files` only checks tracked files; a new file shows "(no files to check) Skipped" until it is staged
- `ruff check --fix` cannot fix E501 (line too long); `ruff format` wraps the lines
- WSL has no ssh-agent: the GitHub key passphrase is asked on every push/pull (optional fix later)
- Old kernel 7.0.0-30 is autoremovable (`sudo apt autoremove` when convenient)
- "1 device has a firmware upgrade" (fwupd) → Hyper-V virtual firmware; ignore
- Log out of the Hyper-V console after any use (a forgotten tty1 login was found and closed on 2026-10-11)
- Largest memory users on the VM: fwupd (~48 MB) and snapd (~45 MB); trimming deferred until RAM gets tight
- After a laptop sleep the VM clock is stepped by chrony within about one poll; journal entries around a step can look out of order
- "active" ≠ ready: about 90 ms between systemd "Started" and the socket being bound (curl right after a restart can fail; seen again in the restore drill; fix in Stage 2)
- `systemd-analyze verify` prints CPUAccounting warnings for Ubuntu's xfs_scrub units; not ours
- `ps` cuts usernames longer than 8 characters (`regassi+`); use `ps -o user:12,…`
- `systemctl --failed` is the only failure signal until Stage 5 → keep it clean: use `systemd-run --collect` (`-G`) for probes; clear leftovers with `sudo systemctl reset-failed 'run-*.service'`
- tar on Ubuntu 26.04 opens directories with `openat2()`; under `RestrictSUIDSGID=yes` it fails with "Cannot stat: Function not implemented" (ENOSYS). Re-test after tar or systemd upgrades.
- Drills and temporary overrides go in `/run/systemd/system/<unit>.d/` (gone on reboot), never in `/etc`

## 4. Stage 1 step plan (weeks 1–5)

1. Host inventory (edition, RAM, disk, WSL)
2. Enable Hyper-V; download and SHA256-verify Ubuntu Server ISO
3. Create VM from PowerShell (Gen2, Secure Boot template, fixed RAM)
4. Install Ubuntu Server 26.04.1; first SSH login; checkpoint
5. Stable name (mshome.net) + SSH alias; verify host key fingerprint
6. SSH key authentication (ed25519, passphrase, ssh-agent)
7. SSH hardening drop-in; remove lxd; checkpoint
8. Package management and patching; unattended upgrades
9. Host firewall (ufw); WSL as second SSH client
10. Repo foundation: GitHub repo (public), README, PROGRESS.md, docs/adr/ (ADR-0001–0007), src/, tests/, Python tooling (uv, ruff, mypy, pytest, pre-commit + gitleaks); first commit 5315a2a
    - 10a. WSL toolchain: uv, git identity, GitHub SSH key
    - 10b. Public GitHub repo; uv project (src layout), ruff/mypy/pytest config, smoke tests
    - 10c. pre-commit hooks + gitleaks, proven with a canary token; .gitignore, .gitattributes
    - 10d. README, PROGRESS.md, ADRs; first commit and push
11. Filesystem, permissions, users/groups: non-login service account regassist, /srv/regassist layout with correct ownership and modes
12. Processes, signals, environment variables: ps/top, process tree, TERM vs KILL vs HUP, /proc/<pid>/environ
13. systemd service + journald: placeholder Python app as a unit running as regassist, bound to 127.0.0.1, with unit hardening; read its logs. Code reaches the VM via git clone with a read-only deploy key (ADR-0006)
    - 13a. Read-only deploy key on the VM; GitHub host key pinned; clone with umask 027
    - 13b. Placeholder app (stdlib): /health, JSON logs to stdout, config from env, SIGTERM, exit codes 0/1/2
    - 13c. Minimal unit (root-owned copy), EnvironmentFile, enable --now, journalctl
    - 13d. Sandbox: 9.2 UNSAFE → 1.1 OK; probe found /dev/shm still shared → private tmpfs
    - 13e. Restart policy, syslog identifier/priorities, crash / bad-config / egress / reboot drills; clock fix (ADR-0010); ADR-0009
14. Bash backup script + systemd service and timer, with retention and a tested restore
    - 14a. Backup design (scope, destination, identity, schedule, retention); /var/backups/regassist 0700; manual tar backup and scratch restore
    - 14b. Script (strict mode, flock, atomic publish, read-back verify, SHA-256, count retention), shellcheck hook, pytest tests against temp dirs; root-owned copy in /usr/local/sbin
    - 14c. Oneshot service (root + CAP_DAC_READ_SEARCH only, read-only FS, no network) + Persistent timer; sandbox bisection found RestrictSUIDSGID vs tar openat2; exit-code contract fix
    - 14d. Restore drills: single file, full data/ (technical RTO 0.34 s), corrupted archive detected
    - 14e. Failure drill via /run drop-in; runbook docs/runbooks/backup-restore.md; ADR-0011; checkpoint 07-backup
15. Networking lab: TCP vs UDP, ports and sockets, TCP handshake in tcpdump; ss, curl -v, dig, ping, traceroute
16. Nginx reverse proxy + self-signed TLS (SAN = regassist-srv01.mshome.net); ufw allow 443
17. End-to-end request trace (Browser → DNS → TCP → TLS → HTTP → Nginx → app), written up in docs/
18. Failure drills: broken port, DNS failure, TLS error, stopped service
19. Corpus: source registry (title, publisher, language, URL, retrieval date, version, usage note, SHA-256) + download script; raw files gitignored
20. Golden set draft: ~20 questions written while reading, tagged dev / held-out
21. Stage 1 gate demonstration

**Stage 1 gate** — explain the full path of a web request · diagnose a broken port · diagnose a DNS problem · explain TLS/HTTPS · manage a Linux service · read service logs · use SSH securely · explain why the app must not run as root.

## 5. Decisions (ADRs in docs/adr/)

| # | Decision | Status |
| --- | --- | --- |
| ADR-0001 | Hyper-V Gen2 VM as the server; Windows OpenSSH + WSL as clients; Ubuntu Server 26.04.1 LTS | Accepted, written |
| ADR-0002 | Reach the VM by DNS name (mshome.net), never by DHCP IP | Accepted, written |
| ADR-0003 | SSH: ed25519 keys only, hardening via drop-in file, no root, allow-list of users | Accepted, written |
| ADR-0004 | Host firewall policy: deny inbound, allow outbound, 22/tcp rate-limited | Accepted, written |
| ADR-0005 | WSL → VM via IPv4 forwarding on the two vEthernet adapters | Accepted, written; automation open |
| ADR-0006 | Dev workspace in WSL Linux filesystem; public GitHub repo as source of truth; VM gets code via git + read-only deploy key | Accepted, written |
| ADR-0007 | Python toolchain (uv, Python 3.13, src layout, ruff, mypy strict, pytest) + pre-commit with gitleaks | Accepted, written |
| ADR-0008 | Service account regassist (system, nologin, no sudo) and /srv/regassist layout; code read-only to the service; deploys with umask 027 | Accepted, written |
| ADR-0009 | systemd unit: root-owned copy, Type=exec, sandbox (exposure 1.1), restart on failure but not on config error, JSON logs with syslog priority; read-only deploy key | Accepted, written |
| ADR-0010 | Time sync: chrony only writer (Hyper-V time sync off), Ubuntu NTS servers, makestep 1 -1; host PTP clock reserved for Azure | Accepted, written |
| ADR-0011 | Local backups: verified tar archives from a sandboxed systemd timer; root reduced to read-search, no network; count-based retention after success; RestrictSUIDSGID off for the backup unit (tar openat2) | Accepted, written |

**Open items**

- Confirm the first scheduled backup (02:30 Riyadh, 27 Oct) and the `Persistent=` catch-up after a laptop sleep or shutdown
- Off-VM backup copy plus encryption at rest: a separate unit with network access and read-only access to the archives (restic or borg as candidates); until then backups share the VHDX and are unencrypted
- Stage 3: application-consistent dumps (Postgres `pg_dump`, Qdrant snapshot API) before archiving
- Stage 4a: the personal-data retention ADR must cover backups (deleted data survives up to 7 days in archives)
- Stage 6: run `systemd-analyze verify` on `deploy/systemd/*` and the backup tests in CI
- Backup runbook: name an owner when Stage 1b defines roles
- Repo license not chosen yet (no LICENSE file = all rights reserved)
- ADR-0005 automation (scheduled task at logon is the candidate)
- Python version re-evaluated in Stage 3 when embedding and OCR libraries are chosen (ADR-0007)
- Optional: ssh-agent in WSL so the GitHub passphrase is asked once per session
- Trim unneeded VM services (fwupd, snapd): decide when RAM gets tight
- Check the AI-102 expiry date and renew it before booking AB-100 (the AB-100 title needs an active associate certification)
- Decide the folder layout for business and architecture documents before Stage 1b (`docs/business/`, `docs/architecture/` proposed)
- Stage 2: readiness — `/ready` endpoint and `Type=notify` (about 90 ms gap between "active" and listening)
- Stage 2: install the package on the server (virtualenv) so /health reports the real version
- Stage 3/4a: widen `IPAddressAllow=` as a reviewed change when the app calls a model API; DNS via 127.0.0.53 remains a possible channel for data leaving the VM
- Host clock: `w32tm /resync` on the corporate network/VPN; raise with IT if it won't sync

## 6. Stage overview (Roadmap v3)

Weeks run Monday to Sunday from 5 October 2026.

| Stage | Weeks | Hours | Status |
| --- | --- | --- | --- |
| 1 — Linux and networking | 1–5 | 36 | In progress (Steps 1–14 done) |
| 1b — Business analysis + PSPO I (exam ~13 Dec 2026) | 6–11 | 72 | Not started |
| 1c — Solution architecture + TOGAF EA (exam ~24 Jan 2027) | 12–16 | 60 | Not started |
| 2 — API, auth, CI v1 | 17–19 | 30 | Not started |
| 3 — Docker and retrieval core | 20–23 | 44 | Not started |
| 4a — Agent, citations, UI (+ document-check workflow, Ollama option) | 24–27 | 40 | Not started |
| 4b — Security and evaluation | 28–29 | 24 | Not started |
| 4c — Transformation and presales pack → v1 milestone (~16 May 2027) | 30–32 | 36 | Not started |
| AB-100 exam block (exam ~4 Jul 2027) | 33–39 | ~75 | Not started |
| 5 — Observability | 40–41 | 24 | Not started |
| 6 — CI/CD complete | 42 | 12 | Not started |
| 7 — Local Kubernetes | 43–45 | 40 | Not started |
| 8a — Azure prep (no account) | 46 | 12 | Not started |
| 8b — Azure 30-day credit window (~23 Aug–19 Sep 2027) | 47–50 | 48 | Not started |
| Buffer | 51–52 | — | — |

Outside Project 1 (see the AI Solutions Architect Path doc): case interview prep (~35 h, before the first consulting interview) and Project 3 — business automation (~50 h), after Project 1.

## 7. Session log

### 2026-10-04 — Steps 1–8

**Done**

- Reviewed project plan; approved Roadmap v2 (scope tiers, $20 cap, local K8s before Azure)
- Host inventory; enabled Hyper-V; downloaded and SHA256-verified Ubuntu 26.04.1 live-server ISO
- Created VM regassist-srv01 from PowerShell; installed Ubuntu Server 26.04.1 (LVM root extended to 37 GB)
- Diagnosed unreachable VM: DHCP lease changed 172.27.51.216 → 172.27.56.52 (ARP "Destination host unreachable")
- SSH via alias `ssh regassist` (regassist-srv01.mshome.net); host key fingerprint verified
- SSH key auth (ed25519, passphrase, ssh-agent; IdentityFile + IdentitiesOnly)
- SSH hardening drop-in 10-hardening.conf; removed yazan from lxd
- Patched 21 packages; unattended security upgrades confirmed
- Checkpoints 01-base-install, 02-hardened-patched

**Key concepts**

- Type 1 vs Type 2 hypervisors; Gen2 VMs, UEFI, Secure Boot templates
- LVM (PV → VG → LV); thin-provisioned disks; checkpoint ≠ backup
- Routing table, longest-prefix match, connected routes; ARP on a local subnet
- DHCP leases keyed by client ID; clients depend on names, not IPs
- SSH host keys, known_hosts, trust-on-first-use vs out-of-band verification
- Public-key auth; passphrase (key at rest) vs agent (key in memory); IdentitiesOnly vs MaxAuthTries
- systemd socket activation for sshd; per-connection sshd-session
- sshd drop-ins: first value wins; `sshd -t` (validate) vs `sshd -T` (effective config)
- Least privilege: lxd group = root without sudo or logs
- apt update vs upgrade vs full-upgrade; signed repos; phased updates; reboot-required
- systemd timers (apt-daily, apt-daily-upgrade); needrestart
- Shell operators `|`, `&&`, `;`

**Validation**

- ISO hash matched SHA256SUMS (26.04.1 live-server line)
- ss: sshd listening on 0.0.0.0:22 and [::]:22
- journalctl: "Accepted publickey … SHA256:SNsk…" matches laptop key
- Password login refused: "Permission denied (publickey)"
- `sshd -T`: passwordauthentication no despite 50-cloud-init.conf saying yes
- 0 upgradable packages; Unattended-Upgrade "1"

**Commit** — none yet (repo created in Step 10)

### 2026-10-05 — Step 9

**Done**

- ufw active and enabled on boot: default deny in / allow out / routed disabled; 22/tcp LIMIT; logging low
- Traced VM DNS path with dig: 127.0.0.53 → 172.27.48.1 → internet
- WSL default distro switched to Ubuntu-24.04 (was docker-desktop)
- WSL → VM connectivity fixed by enabling IPv4 forwarding on both vEthernet adapters (WSL IP 172.21.48.20 seen as source: routed, not NATed)
- WSL client set up: own key id_ed25519_regassist_wsl, alias `ssh regassist`, host key verified
- Checkpoints 03-pre-firewall, 04-firewall

**Decisions**

- Outbound traffic left open (allowlist would need DNS/NTP/apt mirrors) → ADR-0004
- Forwarding resets on reboot/WSL restart; automate later → ADR-0005

**Validation**

- Blocked packets visible with `sudo journalctl -k -g 'UFW BLOCK'`
- Both clients (Windows OpenSSH and WSL) log in with keys

**Commit** — none yet

### 2026-10-06/07 — Step 10 (repo foundation)

**Done**

- WSL toolchain: uv 0.12.23 installed (installer downloaded and inspected before running); project Python 3.13.16 managed by uv
- Git identity set (name, GitHub noreply email, default branch main, pull.ff only)
- GitHub SSH key id_ed25519_github (passphrase) added as an authentication key; GitHub host key verified against the official fingerprints
- VS Code WSL extension installed; project opens in WSL mode
- Public repo Yazanakkad/sovereign-regulatory-assistant created empty; project created with `uv init --package` (src layout, package regassist)
- Dev deps ruff, mypy, pytest, pre-commit; ruff rules E W F I B UP S N SIM RUF (line 100), mypy strict, pytest config in pyproject.toml
- Smoke tests (2); version read from package metadata; `uv run regassist` entry point
- pre-commit: pre-commit-hooks v6.0.0 and gitleaks v8.30.0 (pinned via autoupdate), local ruff/mypy hooks through `uv run`
- .gitignore (.env*, data/raw/, tool caches) and .gitattributes (`* text=auto eol=lf`)
- README, PROGRESS.md, docs/adr/ index + template + ADR-0001–0007
- First commit pushed; upstream origin/main set

**Key concepts**

- Dev box (WSL) vs server (VM); Linux filesystem vs /mnt/c (I/O speed, permission bits)
- `curl | sh` = running remote code with your privileges → download, inspect, then run
- One key per purpose; account key (read/write all repos) vs deploy key (one repo, read-only)
- Trust-on-first-use for GitHub; answering the prompt with the [fingerprint] option
- Noreply email: git history is public and permanent
- GitHub Free: rulesets/branch protection only on public repos → repo public from day 1
- uv: lockfile, dev dependency group, `uv run`; src layout; single source of truth for the version
- ruff S rules (bandit security checks); mypy strict; W292 / POSIX final newline
- pre-commit hooks are a seatbelt (bypassable with --no-verify), CI is the gate; pinned hook revisions as a supply-chain control; local hooks bound to uv.lock
- Leaked secret → rotate first, then clean history
- ADR structure (context, decision, alternatives, consequences); ADRs superseded, never edited
- Root commit, upstream tracking (push -u), conventional commit prefixes

**Validation**

- `ssh -T git@github.com` → "Hi Yazanakkad! You've successfully authenticated…"
- GitHub shows key fingerprint SHA256:mtuos…TpV8, matching ssh-keygen
- ruff check / ruff format --check / mypy strict / pytest 2 passed; `uv run regassist` → regassist 0.1.0
- `pre-commit run --all-files`: all hooks Passed
- Canary: fake ghp_ token → gitleaks Failed, RuleID github-pat, output redacted (expected)
- Commit: all hooks Passed; push created main on GitHub; working tree clean

**Decisions**

- Repo public from day 1 → ADR-0006
- Python 3.13 via uv; toolchain and commit checks → ADR-0007

**Commit** — 5315a2a chore: repo foundation, Python tooling, pre-commit and ADRs 0001-0007

### 2026-10-11 — Steps 11–12

**Done**

- Service account regassist created with `useradd --system --user-group --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin` (UID 999, GID 983)
- Layout created with `install -d` (owner, group and mode set in one step): /srv/regassist, app/ (setgid), data/, /etc/regassist
- umask trap shown: with umask 0002 a file in app/ is rw-rw-r-- (service group could modify code); with `(umask 027; …)` it is rw-r-----
- Eight boundary tests as regassist; ADR-0008 written with a verification table and added to the ADR index
- Checkpoint 05-service-account
- Inspected own shell: process tree back to PID 1, /proc/$$/status, ps, top, systemd-cgls
- Signal demos: HUP handled (keeps running), TERM handled (exit 0), default TERM (143), TERM ignored then KILL (137), Ctrl+C (130)
- Found and closed a forgotten tty1 console login (session-1.scope) with `sudo loginctl terminate-session 1`
- Environment demos: export vs shell variable, one-command variables, /proc/<pid>/environ snapshot and permissions, sudo env_reset, systemd service environment

**Key concepts**

- The kernel sees UIDs/GIDs, not names; /etc/passwd (7 fields, world-readable) vs /etc/shadow (hashes, root/shadow only)
- System users (UID < 1000) vs regular users; user private groups; group membership = privilege
- Three independent locks on regassist: locked password, nologin, sshd AllowUsers; none of them stops root or systemd from running a process as it
- Octal modes (r4 w2 x1; leading 4 setuid / 2 setgid / 1 sticky); on directories r = list, x = traverse, w+x = create/delete entries; deleting depends on the directory
- Setgid directories pass their group to new entries; umask removes bits from 666/777; scoped umask in a subshell
- The service can read its code but not write it; only data/ is writable
- Test as the identity that runs (`sudo -u regassist`); file permissions can't close /tmp (sticky, world-writable) → systemd sandbox in Step 13
- fork + exec; PID 1 starts services and reaps orphans (the container PID 1 problem → --init); kernel threads in brackets
- Four UIDs (real/effective/saved/filesystem); process states R S D Z T; RSS vs VSZ; read avail, not free; load average vs nproc
- sshd privilege separation ([priv] as root, session as the user); `systemd --deserialize` = systemd re-exec after upgrades
- Cgroups: systemd tracks every process of a unit; the basis of Docker --memory and Kubernetes requests/limits
- Signals: TERM (graceful), KILL (can't be caught), HUP (reload by convention), INT (Ctrl+C to the foreground process group); exit 128+N
- Graceful shutdown = TERM → grace period → KILL (systemd 90 s, Docker 10 s, Kubernetes 30 s); exit 137 in containers usually means the OOM killer
- Interactive bash abandons the rest of a `;` list after Ctrl+C
- Environment: copied at fork, parent→child only; `VAR=x cmd`; /proc/<pid>/environ is a snapshot readable by the same UID and root
- sudo env_reset (keep-list for harmless variables, adds SUDO_*) and secure_path; systemd services start with a near-empty environment (INVOCATION_ID, JOURNAL_STREAM, memory pressure)
- Config in env vars, secrets in files only the service can read (later: LoadCredential=, Kubernetes Secret volumes, Key Vault + Managed Identity)

**Validation**

- `getent passwd regassist` → …:999:983:…:/nonexistent:/usr/sbin/nologin; `passwd -S` → L; `sudo su - regassist` → "This account is currently not available."
- stat → 755 root:root, 2750 yazan:regassist (drwxr-s---), 750 regassist:regassist, 750 root:regassist; `namei -l` shows traversal on every parent
- Boundary tests: write data/ OK · write app/ denied · read app/ OK · write /etc/regassist denied · yazan reads data/ without sudo denied · read /home/yazan denied · `sudo -l -U regassist` not allowed · write /tmp OK (accepted gap)
- pstree: systemd(1) → sshd → sshd-session [priv] → sshd-session yazan@pts/0 → bash; /proc/$$/status Uid: 1000 ×4
- Load 0.13 on 2 vCPUs; 2855 MiB available of 3398 MiB; 0 zombies
- Exit codes observed: 0, 143, 137, 130; the TERM-ignoring process stayed alive in ps until KILL
- loginctl: 3 sessions → 2 (tty1 session closed)
- /proc/<pid>/environ: snapshot showed the original value; mode -r--------; regassist denied, root allowed
- `sudo -u regassist env`: no DEMO_VAR; sudoers has env_reset and secure_path; cron environment contains only systemd-provided variables

**Decisions**

- ADR-0008: dedicated service account and /srv/regassist layout; code owned by the deploy identity (yazan) and read-only to the service; deploys with a scoped umask 027; admin access to service data via sudo
- /tmp write access accepted at the file-permission layer; closed in Step 13 with PrivateTmp=, ProtectSystem=strict, ReadWritePaths=
- Secrets for the service will live in /etc/regassist/regassist.env (root:regassist 0640), not in shell exports
- Trimming fwupd / snapd deferred (open item)

**Commit** — a95b5b4 docs(adr): add ADR-0008 service account and filesystem layout · b1181e0 docs(adr): add ADR-0008 to index

### 2026-10-24 — Plan change: Roadmap v3

**Why** — career direction moved to AI Solutions Architect / AI consulting (business + architecture + build). Real Riyadh job posts showed gaps in requirements and business cases, architecture documentation, agentic workflows and presales material.

**Done**

- Roadmap updated in place to v3 (same artifact link); doc renamed "Roadmap v3"
- New Stage 1b — Business analysis + PSPO I (weeks 6–11): stakeholder map, BPMN as-is process, opportunity assessment, BRD, user stories, NFRs, requirement IDs with traceability, business case, value stream and capability map
- New Stage 1c — Solution architecture + TOGAF EA (weeks 12–16): architecture document, ArchiMate views in Archi, transition roadmap, PDPL/SAMA/NCA compliance matrix, multi-cloud mapping, responsible AI and risk register
- Stage 4a: multi-step document-check agent workflow (Must) and Ollama sovereign option on CPU (Should)
- Stage 4b: hallucination rate and p50/p95 latency added to the eval report
- New Stage 4c — Transformation and presales pack (weeks 30–32): roadmap, KPIs, RFP response, SOW, cost estimate / BOM, delivery estimate, GPU sizing note, executive deck, recorded demo; v1 milestone moved here (~16 May 2027)
- AB-100 exam block in weeks 33–39 (exam ~4 Jul 2027)
- Stage 1 extended to weeks 1–5 (Step 12 of 21 done at the end of week 3)
- Plan length 28 → 52 weeks; Azure credit window moved to ~23 Aug–19 Sep 2027
- Exam map: AI-103, AZ-104 and Terraform Associate replaced by PSPO I, TOGAF EA Foundation and AB-100; Terraform kept as a skill

**Decisions**

- Business layer as its own stage right after Stage 1, so requirements drive the build
- Keep the full technical scope and accept the longer plan
- Exams interleaved: PSPO I in 1b, TOGAF EA in 1c, AB-100 after v1

**Commit** — committed with the 2026-10-26 PROGRESS update

### 2026-10-26 — Step 13 (13a–13e)

**Done**

- 13a: read-only deploy key on the VM (owned by yazan); GitHub ED25519 host key fetched with ssh-keyscan, fingerprint checked, pinned; repo cloned into /srv/regassist/app with umask 027
- 13b: placeholder service (stdlib): /health, JSON 404, JSON logs to stdout, config from REGASSIST_HOST/PORT, graceful SIGTERM, exit codes 0/1/2, Server header without Python version; `__version__` falls back to 0.0.0+source when not installed; 10 tests
- 13c: unit `deploy/systemd/regassist-app.service` installed as a root-owned copy; /etc/regassist/regassist.env (root:regassist 0640); enabled and started
- 13d: sandbox (ProtectSystem=strict, PrivateTmp/Devices, no capabilities, NoNewPrivileges, seccomp filter, localhost-only IP); exposure 9.2 → 1.1; probe found /dev/shm still shared → TemporaryFileSystem=/dev/shm
- 13e: Restart=on-failure, RestartSec=2, RestartPreventExitStatus=2, StartLimitBurst=5/60 s; SyslogIdentifier; syslog priority prefix when JOURNAL_STREAM is set; 13 tests
- Drills: SIGKILL crash, bad config, egress, operator log queries, reboot
- Clock incident: VM clock 36 min slow after a pause (chrony could only slew); Windows host 189 s fast (domain DC unreachable since 21 Oct) and copied into the VM at boot → Hyper-V time sync disabled, chrony makestep 1 -1 drop-in; drill proved the step
- ADR-0009 and ADR-0010 written; checkpoint 06-systemd-service

**Key concepts**

- Deploy key vs account key; key protection matched to its scope; ssh-keyscan + out-of-band fingerprint; IdentitiesOnly
- Three identities: yazan deploys, regassist runs, root installs units; unit file root-owned outside the code directory (otherwise deploy access = root)
- The runtime contract: logs to stdout, config from the environment, SIGTERM, meaningful exit codes; same under systemd, Docker and Kubernetes
- Signal handlers stay tiny; shutdown() from another thread; Python skips .pyc when the code directory is read-only
- Unit sections, enable vs start, daemon-reload, Type=exec vs simple vs notify, After= is ordering only
- EnvironmentFile read by systemd as root; journald trusted fields (_UID, _PID, _SYSTEMD_UNIT, _BOOT_ID); PPID 1
- Defence in depth: file permissions + sandbox; ProtectSystem=strict + ReadWritePaths allow-list; PrivateTmp; capabilities; NoNewPrivileges; seccomp; IPAddressDeny as egress control (DNS caveat); MemoryDenyWriteExecute vs JIT
- The security score is a heuristic; probes prove the boundaries (the score missed /dev/shm); nsenter enters the mount namespace only
- Restart=on-failure vs always; RestartPreventExitStatus; start limits ≈ CrashLoopBackOff; stop vs kill
- Syslog priorities 0–7, `<N>` prefix, JOURNAL_STREAM; journalctl -u / -p / -o cat / -b -1 / --since; persistent journal and size caps
- "Active" ≠ ready (readiness probes)
- Time: RTC vs system clock; step vs slew; makestep; two clock writers fight; Hyper-V PTP clock (right on Azure, wrong on a drifting laptop); Kerberos 5-minute skew; measure durations with a monotonic clock
- Pre-commit hooks that modify files abort the commit; `;` vs `&&` for commit + push

**Validation**

- `ssh -T` → "Hi Yazanakkad/sovereign-regulatory-assistant!"; `git push --dry-run` → "marked as read only"; GitHub key fingerprint SHA256:IL5YD46…UTVo, Read-only
- Clone: app 2750, README 640, no g+w files, no __pycache__; regassist can read the code, can't write it or read ~/.ssh
- Manual run as regassist: 200 with `Server: regassist`, JSON 404, 127.0.0.1:8000, SIGTERM → exit 0, bad port → exit 2
- Unit: active, PPID 1, `_UID 999`, `_CAP_EFFECTIVE 0`, `_TRANSPORT stdout`; stop → SIGTERM → "Deactivated successfully"
- Probe as regassist: before — /tmp, /var/tmp, /dev/shm shared, /home listable; after — all private, /home denied, only data/ writable
- Crash: new PID after 2 s, NRestarts=1; bad config: failed, 2/INVALIDARGUMENT, no restart, found with `-p err`; egress: localhost 200, github.com timeout (28)
- Reboot: active without login; previous boot ends with SIGTERM stop; two boots listed
- Time: `chronyd -p` shows makestep 1 -1 last; drill "wrong by 120.01 s" → "stepped by 120.01 s"; final offset 1 ms, Leap Normal

**Decisions**

- ADR-0009: systemd unit, sandbox, restart and logging; read-only deploy key
- ADR-0010: chrony only clock writer, NTS, makestep 1 -1; host PTP clock reserved for Azure (Stage 8)
- Host Windows clock not reconfigured (employer domain); resync on the corporate network/VPN

**Commit** — d1f04b4 feat(server): placeholder HTTP service · 614a93e feat(deploy): systemd unit · 35635ca feat(deploy): harden the systemd unit · eb66410 fix(deploy): private /dev/shm · 4a99b89 feat(deploy): restart policy, syslog identifier and log priorities · cf7db45 docs(adr): ADR-0009 and ADR-0010 · 9294a70 docs(progress): Roadmap v3 and Step 13

**Next step** — Stage 1 → Step 14: Bash backup script (data/ and /etc/regassist) run by a systemd service and timer, with retention and a tested restore

### 2026-10-26/27 — Step 14 (14a–14e)

**Done**

- 14a: backup design (scope data/ + /etc/regassist, code excluded); /var/backups/regassist root:root 0700; demo data seeded as regassist; manual tar backup, listing by name and by UID, scratch restore matched including owners and modes; root's umask left the manual archive 644
- 14b: `deploy/backup/regassist-backup.sh` — strict mode, flock, temp file → read-back verify → SHA-256 → atomic rename → sync, count retention after success that never prunes the new archive, logfmt logs with syslog priorities; shellcheck-py pre-commit hook; pytest tests against temporary directories; root-owned copy `/usr/local/sbin/regassist-backup`; archives 0600
- 14c: `regassist-backup.service` (oneshot, root with only CAP_DAC_READ_SEARCH, ProtectSystem=strict, one writable path, no network, seccomp) + `regassist-backup.timer` (02:30 Asia/Riyadh, Persistent); capability probes with systemd-run; first service run failed "Cannot stat: Function not implemented" → bisected the sandbox (kern group → RestrictSUIDSGID) → strace showed tar uses openat2 → option removed from the backup unit with compensating controls; exit-code contract fixed (tool failures → 1 with cause_exit) plus a regression test
- 14d: restore drills — single file with --keep-old-files; full data/ restore with the app stopped and restarted, technical RTO 0.34 s, DATA MATCHES; corrupted copy detected by checksum and gzip CRC
- 14e: failure drill via a /run drop-in (KEEP=0 → failed, exit 2, nothing pruned) and recovery; cleared leftover failed probe units; runbook `docs/runbooks/backup-restore.md`; ADR-0011 and index entry; checkpoint 07-backup

**Key concepts**

- Back up only what can't be recreated; backup vs checkpoint vs replication; 3-2-1 rule; RPO/RTO as business decisions (NFRs in Stage 1b)
- Backups are the most sensitive copy; personal-data retention must include backups (PDPL)
- tar stores user names and numeric IDs and restores by name as root; relative members with `--directory /`
- File copies of live databases are inconsistent → application-consistent dumps
- Bash strict mode (`-euo pipefail`); atomic publish via same-filesystem rename; read-back verification; checksums as audit evidence; flock released by the kernel when the process dies
- Count-based retention, only after success, never the newest archive (clock-jump safe)
- Exit codes as an interface; deliberate vs unexpected failures; ERR trap plus `exit` inside an EXIT trap
- Root = about 40 capabilities; CAP_DAC_READ_SEARCH vs CAP_DAC_OVERRIDE; capabilities alone don't stop root writing root-owned files → ProtectSystem
- No network for a local backup job; the off-site copy belongs in a separate unit
- Type=oneshot semantics (start blocks; default start timeout infinite); OnCalendar with a time zone; Persistent catch-up; static units started by timers
- ENOSYS from systemd seccomp; RestrictSUIDSGID can't inspect openat2's mode; bisecting a sandbox; strace
- Unit tests outside the sandbox ≠ integration test inside it
- Restore order: stop writer → move aside → verify → extract → start → health check → compare → clean up; a running service's sandbox keeps a bind mount of the old directory
- Technical RTO vs real RTO (detection and decision time excluded)
- /run vs /etc drop-ins; `systemctl --failed` hygiene (alert fatigue); `systemd-run --collect`
- Runbook (how, kept current, drilled) vs ADR (why, superseded not edited)

**Validation**

- Manual restore: RESTORE MATCHES; 640 regassist:regassist and 640 root:regassist after round trip
- pytest 22 passed; shellcheck Passed; ruff and mypy clean
- First script run: archive, .sha256 and .lock all 0600; `sha256sum -c` OK; KEEP=1 pruned exactly one archive; identical SHA-256 for unchanged data
- Capability probes: no caps → read denied; read-search only → read OK, write denied; /etc writable without ProtectSystem, read-only with it
- Bisection: all and kern fail, fs/net/sched pass; only RestrictSUIDSGID=yes fails; strace: `openat2(4, "srv/regassist/", … resolve=0)`
- Service run: status=0/SUCCESS, TriggeredBy timer, exposure 1.3 OK; calendar next elapse 23:30 UTC
- Restore drills: single file 640 regassist:regassist with original content; full restore RTO 0.34 s, 750 regassist:regassist, DATA MATCHES, app active (one curl refused before ready — known gap); corrupted copy hash a35d… vs recorded 3d80…, gzip CRC error, tar exit 2
- Failure drill: status=2, unit listed in --failed, config_error and backup_failed exit=2 logged, archives 3 → 3; after cleanup exit=0, 0 failed units, 4 archives
- Repo: runbook present; checkpoint list ends with 07-backup

**Decisions**

- ADR-0011: local verified backups via a sandboxed systemd timer; root reduced to read-search, no network; count retention after success; gzip; RestrictSUIDSGID off for the backup unit only
- Backups stay on the same disk and unencrypted for now; off-VM copy with encryption is an open item
- Probe units use `systemd-run --collect` from now on
- `docs/runbooks/` holds operational runbooks (Stage 7 failure runbooks go there too)

**Commit** — daee1ea feat(backup): backup script with lock, verification, checksum and retention · 744ae6b feat(deploy): sandboxed backup service and daily timer · 6939949 fix(deploy): drop RestrictSUIDSGID from backup unit; tar needs openat2 · d50416a fix(backup): keep the exit-code contract; report tool failures as 1 with cause · 1bb1649 test(backup): regression test for the exit-code contract · f0ad4c1 docs: backup and restore runbook; ADR-0011 backups · cf7db45 docs(adr): add ADR-0011 to index · (this file) docs(progress): Step 14 backups

**Next step** — Confirm the 02:30 scheduled backup ran; then Stage 1 → Step 15: networking lab (TCP vs UDP, ports and sockets, TCP handshake in tcpdump; ss, curl -v, dig, ping, traceroute). Pacing: Steps 15–21 remain in weeks 4–5.
