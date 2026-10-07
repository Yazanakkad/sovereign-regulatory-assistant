# PROGRESS — Project 1: Sovereign Regulatory AI Assistant

> **For a new chat:** read this whole file first. Continue from **Current position**.
> Full plan: *Project 1 — Roadmap v2* (Project files, and https://claude.ai/code/artifact/69380837-fa7a-410d-bff3-ced256ff6bf0).

---

## 1. Current position

| | |
|---|---|
| **Stage** | Stage 1 — Linux and networking (weeks 1–3, 36 h) |
| **Last completed** | Step 9 — host firewall (ufw) + WSL as second SSH client |
| **Next step** | **Step 10 — Repo foundation + first ADRs** (see section 4) |
| **Budget spent** | $0 of $20 (OpenAI $0 / 5 · Azure $0 / 10 reserve · contingency $0 / 5) |

---

## 2. How we work (rules for every chat)

- **One step at a time.** Every step has exactly: **What · Why · Do this · Check · What I should understand · Exam map**.
- **Gates over commands.** A stage ends only when its gate is demonstrated.
- **When something fails:** diagnose → likely cause → smallest diagnostic command → wait for output → fix → re-test. Don't list five fixes at once.
- **No silent architecture changes.** Explain why, what changes, roadmap impact, then ask for approval.
- **Cost:** never create a chargeable resource without naming it, checking current pricing, and getting approval. Hard cap $20 total.
- **Current facts are looked up** (Azure services, models, pricing, regions, exam objectives) from official sources.
- **Commands:** prefer one-liners joined with `;` (pastes sometimes lose line breaks). Work over SSH, not the Hyper-V console.
- **Exam map** list: AI-103 · AZ-104 · HashiCorp Terraform Associate · TOGAF Foundation · Kubernetes curriculum (reference). Otherwise: "No direct exam mapping — production engineering skill."
- **End of session:** the assistant gives an update block; paste it into section 7 and update sections 1, 3 and 4.

---

## 3. Environment snapshot (current state)

**Host laptop**
- Windows 11 Pro (build 26200), i7-1355U 10 cores / 12 threads, 40 GB RAM (~27 GB free after reboot), 308 GB free disk
- Hyper-V enabled; WSL 2.6.3 — distros: `Ubuntu-24.04` (default), `docker-desktop`
- Docker Desktop installed (used from Stage 3); no `.wslconfig` yet (memory cap added in Stage 3)

**VM `regassist-srv01`**
- Hyper-V Gen2, 2 vCPU, 4 GB fixed RAM, 40 GB VHDX at `C:\VMs\regassist-srv01\`, automatic checkpoints off
- Secure Boot on, template `MicrosoftUEFICertificateAuthority`; ISO detached, boots from disk
- Ubuntu Server 26.04.1 LTS, kernel 7.0.0-38-generic, LVM root 37 GB, swap 3.8 GiB
- Fully patched; unattended security upgrades on (`apt-daily*` timers)

**Network**
- VM `eth0`: DHCP from Default Switch — currently `172.27.56.52/20` (**can change**; always use the name)
- Name: `regassist-srv01.mshome.net` (Default Switch DNS) · host side of switch: `172.27.48.1`
- VM DNS path: app → `127.0.0.53` (systemd-resolved) → `172.27.48.1` (Windows host) → internet
- WSL → VM works via IPv4 forwarding on `vEthernet (WSL (Hyper-V firewall))` + `vEthernet (Default Switch)`; VM sees WSL's own IP (routed, not NATed)

**Access**
- User `yazan` (groups include `sudo`, `adm`; removed from `lxd`)
- Server host key: ED25519 `SHA256:GqrCzbHA3iwDOCyHn8h/dQyEvRePV1k44z8VlGsXs2Q`
- Windows client: key `~/.ssh/id_ed25519_regassist` (passphrase, Windows ssh-agent), alias `ssh regassist`
- WSL client: key `~/.ssh/id_ed25519_regassist_wsl` (comment `yazan@wsl-regassist`), alias `ssh regassist`
- sshd drop-in `/etc/ssh/sshd_config.d/10-hardening.conf`: keys only, no root, `AllowUsers yazan`, `MaxAuthTries 3`, no X11

**Firewall (ufw)**
- Active, starts on boot; default deny incoming / allow outgoing / routed disabled
- `22/tcp LIMIT`; logging low → blocked packets: `sudo journalctl -k -g 'UFW BLOCK'`

**Hyper-V checkpoints:** `01-base-install`, `02-hardened-patched`, `03-pre-firewall`, `04-firewall`

**Known quirks**
- Hyper-V console can't paste (keyboard layout) → use SSH only
- Pastes may join lines → use the code block copy button / Windows Terminal, or `;` one-liners
- WSL → VM forwarding resets after Windows reboot or WSL restart → re-run (Admin PowerShell):
  `Set-NetIPInterface -InterfaceAlias "vEthernet (WSL (Hyper-V firewall))","vEthernet (Default Switch)" -AddressFamily IPv4 -Forwarding Enabled`
  (automation pending — see ADR list)
- Old kernel 7.0.0-30 is autoremovable (`sudo apt autoremove` when convenient)
- "1 device has a firmware upgrade" (fwupd) → Hyper-V virtual firmware; ignore

---

## 4. Stage 1 step plan

- [x] 1. Host inventory (edition, RAM, disk, WSL)
- [x] 2. Enable Hyper-V; download and SHA256-verify Ubuntu Server ISO
- [x] 3. Create VM from PowerShell (Gen2, Secure Boot template, fixed RAM)
- [x] 4. Install Ubuntu Server 26.04.1; first SSH login; checkpoint
- [x] 5. Stable name (`mshome.net`) + SSH alias; verify host key fingerprint
- [x] 6. SSH key authentication (ed25519, passphrase, ssh-agent)
- [x] 7. SSH hardening drop-in; remove `lxd`; checkpoint
- [x] 8. Package management and patching; unattended upgrades
- [x] 9. Host firewall (ufw); WSL as second SSH client
- [ ] **10. Repo foundation:** GitHub repo, README, this PROGRESS.md, `docs/adr/` with first ADRs (see section 5), `src/`, `tests/`, Python tooling (uv, ruff, pytest, pre-commit); first commit
- [ ] 11. Filesystem, permissions, users/groups: non-login service account `regassist`, `/srv/regassist` layout with correct ownership and modes
- [ ] 12. Processes, signals, environment variables: ps/top, process tree, TERM vs KILL vs HUP, `/proc/<pid>/environ`
- [ ] 13. systemd service + journald: placeholder Python app as a unit running as `regassist`, bound to 127.0.0.1, with unit hardening; read its logs
- [ ] 14. Bash backup script + systemd service and timer, with retention and a tested restore
- [ ] 15. Networking lab: TCP vs UDP, ports and sockets, TCP handshake in tcpdump; ss, curl -v, dig, ping, traceroute
- [ ] 16. Nginx reverse proxy + self-signed TLS (SAN = `regassist-srv01.mshome.net`); ufw allow 443
- [ ] 17. End-to-end request trace (Browser → DNS → TCP → TLS → HTTP → Nginx → app), written up in `docs/`
- [ ] 18. Failure drills: broken port, DNS failure, TLS error, stopped service
- [ ] 19. Corpus: source registry (title, publisher, language, URL, retrieval date, version, usage note, SHA-256) + download script; raw files gitignored
- [ ] 20. Golden set draft: ~20 questions written while reading, tagged dev / held-out
- [ ] 21. **Stage 1 gate** demonstration

**Stage 1 gate** — explain the full path of a web request · diagnose a broken port · diagnose a DNS problem · explain TLS/HTTPS · manage a Linux service · read service logs · use SSH securely · explain why the app must not run as root.

---

## 5. Decisions (ADRs to write in Step 10)

| # | Decision | Status |
|---|---|---|
| ADR-0001 | Hyper-V Gen2 VM as the server; Windows OpenSSH + WSL as clients; Ubuntu Server 26.04.1 LTS | Decided, ADR to write |
| ADR-0002 | Reach the VM by DNS name (`mshome.net`), never by DHCP IP | Decided, ADR to write |
| ADR-0003 | SSH: ed25519 keys only, hardening via drop-in file, no root, allow-list of users | Decided, ADR to write |
| ADR-0004 | Host firewall policy: deny inbound, allow outbound (outbound allowlist would need DNS/NTP/apt mirrors), `22/tcp` rate-limited | Decided, ADR to write |
| ADR-0005 | WSL → VM via IPv4 forwarding on the two vEthernet adapters; automation after reboot pending | Decided, automation open |

---

## 6. Stage overview (Roadmap v2)

| Stage | Weeks | Hours | Status |
|---|---|---|---|
| 1 — Linux and networking | 1–3 | 36 | **In progress** (Steps 1–9 done) |
| 2 — API, auth, CI v1 | 4–6 | 30 | Not started |
| 3 — Docker and retrieval core | 7–10 | 44 | Not started |
| 4a — Agent, citations, UI | 11–13 | 30 | Not started |
| 4b — Security and evaluation → **v1 milestone** (~17 Jan 2027) | 14–15 | 24 | Not started |
| 5 — Observability | 16–17 | 24 | Not started |
| 6 — CI/CD complete | 18 | 12 | Not started |
| 7 — Local Kubernetes | 19–21 | 40 | Not started |
| 8a — Azure prep (no account) | 22 | 12 | Not started |
| 8b — Azure 30-day credit window (~8 Mar–4 Apr 2027) | 23–26 | 48 | Not started |
| Buffer | 27–28 | — | — |

---

## 7. Session log

### 2026-10-04 — Steps 1–8

**Done**
- Reviewed project plan; approved Roadmap v2 (scope tiers, $20 cap, local K8s before Azure)
- Host inventory; enabled Hyper-V; downloaded and SHA256-verified Ubuntu 26.04.1 live-server ISO
- Created VM `regassist-srv01` from PowerShell; installed Ubuntu Server 26.04.1 (LVM root extended to 37 GB)
- Diagnosed unreachable VM: DHCP lease changed `172.27.51.216` → `172.27.56.52` (ARP "Destination host unreachable")
- SSH via alias `ssh regassist` (`regassist-srv01.mshome.net`); host key fingerprint verified
- SSH key auth (ed25519, passphrase, ssh-agent; `IdentityFile` + `IdentitiesOnly`)
- SSH hardening drop-in `10-hardening.conf`; removed `yazan` from `lxd`
- Patched 21 packages; unattended security upgrades confirmed
- Checkpoints `01-base-install`, `02-hardened-patched`

**Key concepts**
- Type 1 vs Type 2 hypervisors; Gen2 VMs, UEFI, Secure Boot templates
- LVM (PV → VG → LV); thin-provisioned disks; checkpoint ≠ backup
- Routing table, longest-prefix match, connected routes; ARP on a local subnet
- DHCP leases keyed by client ID; clients depend on names, not IPs
- SSH host keys, known_hosts, trust-on-first-use vs out-of-band verification
- Public-key auth; passphrase (key at rest) vs agent (key in memory); `IdentitiesOnly` vs `MaxAuthTries`
- systemd socket activation for sshd; per-connection `sshd-session`
- sshd drop-ins: first value wins; `sshd -t` (validate) vs `sshd -T` (effective config)
- Least privilege: `lxd` group = root without sudo or logs
- apt update vs upgrade vs full-upgrade; signed repos; phased updates; reboot-required
- systemd timers (`apt-daily`, `apt-daily-upgrade`); needrestart
- Shell operators `|`, `&&`, `;`

**Validation**
- ISO hash matched `SHA256SUMS` (26.04.1 live-server line)
- `ss`: sshd listening on `0.0.0.0:22` and `[::]:22`
- `journalctl`: "Accepted publickey … SHA256:SNsk…" matches laptop key
- Password login refused: "Permission denied (publickey)"
- `sshd -T`: `passwordauthentication no` despite `50-cloud-init.conf` saying yes
- 0 upgradable packages; `Unattended-Upgrade "1"`

**Commit** — none yet (repo created in Step 10)

### 2026-10-05 — Step 9

**Done**
- ufw active and enabled on boot: default deny in / allow out / routed disabled; `22/tcp LIMIT`; logging low
- Traced VM DNS path with `dig`: `127.0.0.53` → `172.27.48.1` → internet
- WSL default distro switched to `Ubuntu-24.04` (was `docker-desktop`)
- WSL → VM connectivity fixed by enabling IPv4 forwarding on both vEthernet adapters (WSL IP `172.21.48.20` seen as source: routed, not NATed)
- WSL client set up: own key `id_ed25519_regassist_wsl`, alias `ssh regassist`, host key verified
- Checkpoints `03-pre-firewall`, `04-firewall`

**Decisions**
- Outbound traffic left open (allowlist would need DNS/NTP/apt mirrors) → ADR-0004
- Forwarding resets on reboot/WSL restart; automate later → ADR-0005

**Validation**
- Blocked packets visible with `sudo journalctl -k -g 'UFW BLOCK'`
- Both clients (Windows OpenSSH and WSL) log in with keys

**Commit** — none yet

**Next step** — Stage 1 → Step 10: repo foundation + first ADRs
