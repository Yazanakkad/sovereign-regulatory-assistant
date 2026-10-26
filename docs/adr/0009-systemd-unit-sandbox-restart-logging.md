# ADR-0009: systemd unit for the service — sandbox, restart policy and logging

- **Status:** Accepted
- **Date:** 2026-10-26
- **Related:** ADR-0006 (code via git + deploy key), ADR-0008 (service account and layout)

## Context

From Step 13 the application runs on the VM as a long-running service. It must start at
boot, recover from crashes, stop cleanly, and leave logs an operator can filter. ADR-0008
left a known gap: file permissions cannot stop the service writing to the shared `/tmp`,
`/var/tmp` and `/dev/shm`. If the app is ever compromised (dependency CVE, malicious
document, prompt injection reaching a tool), file permissions are the only boundary.

The same runtime contract (config from the environment, logs to stdout, SIGTERM, exit
codes) must carry over unchanged to Docker (Stage 3) and Kubernetes (Stage 7).

## Decision

1. **Code delivery:** a read-only GitHub deploy key on the VM, owned by `yazan`
   (`~/.ssh/id_ed25519_deploy_regassist`, no passphrase: its scope is read-only access to one
   public repo). GitHub's ED25519 host key is pinned with `ssh-keyscan` after an out-of-band
   fingerprint check. Deploys run `(umask 027; git -C /srv/regassist/app pull)`.
2. **Unit file in the repo** (`deploy/systemd/regassist-app.service`), installed as a
   **root-owned copy** in `/etc/systemd/system/` — never a symlink into `app/`, so the deploy
   identity cannot change `User=` or the sandbox.
3. **Runtime:** `Type=exec`; `User=`/`Group=regassist`; config from
   `EnvironmentFile=/etc/regassist/regassist.env` (`root:regassist 0640`); standard-library
   Python on the system interpreter via `PYTHONPATH` (no virtualenv until Stage 2).
4. **App contract:** binds `127.0.0.1:8000`; JSON logs to stdout; graceful stop on SIGTERM;
   exit codes `0` clean, `1` cannot bind, `2` invalid configuration.
5. **Sandbox:**
   - Filesystem: `ProtectSystem=strict` + `ReadWritePaths=/srv/regassist/data`,
     `ProtectHome`, `PrivateTmp`, `PrivateDevices`, private `/dev/shm`
     (`TemporaryFileSystem=`), `UMask=0077`.
   - Privileges: empty `CapabilityBoundingSet=`, `NoNewPrivileges`, `RestrictSUIDSGID`.
   - Kernel and process: `ProtectKernel*`, `ProtectControlGroups`, `ProtectClock`,
     `ProtectHostname`, `ProtectProc=invisible`, `ProcSubset=pid`, `LockPersonality`,
     `MemoryDenyWriteExecute`, `RestrictRealtime`, `RestrictNamespaces`, `RemoveIPC`.
   - System calls: `@system-service` minus `@privileged @resources`, native architecture only.
   - Network: `AF_INET AF_INET6 AF_UNIX` only; `IPAddressDeny=any` + `IPAddressAllow=localhost`.
6. **Restart policy:** `Restart=on-failure`, `RestartSec=2`, `RestartPreventExitStatus=2`
   (no restart loop on bad config), `StartLimitBurst=5` per `StartLimitIntervalSec=60`.
7. **Logging:** `SyslogIdentifier=regassist-app`; the app prefixes each line with its syslog
   priority (`<N>`) only when `JOURNAL_STREAM` is set, so `journalctl -p err` works and other
   runtimes get plain JSON.

## Alternatives considered

- **Run as `yazan` or root:** rejected (ADR-0008).
- **`systemctl link` to the unit in `app/`:** rejected — a code-deploy permission would become
  root-equivalent.
- **Account SSH key or anonymous HTTPS clone on the VM:** the account key reaches every repo
  read/write; anonymous HTTPS works only while the repo is public. The deploy key keeps the
  same path if the repo goes private.
- **`Type=simple`:** reports success even when the exec fails. **`Type=notify`:** true
  readiness, but needs `sd_notify` in the app — revisit in Stage 2.
- **`Restart=always`:** would restart configuration errors and deliberate clean exits.
- **App-managed log files:** rejected; stdout + journald (and later Docker/Kubernetes) own logs.

## Consequences

- Exposure score 9.2 UNSAFE → 1.1 OK; the score missed `/dev/shm`, which only a probe found.
  Boundaries are verified by probe, not by score.
- Egress is blocked. When the app calls a model API (Stage 3/4a), `IPAddressAllow=` must be
  widened as a reviewed change. DNS through the local resolver (127.0.0.53) remains possible.
- `MemoryDenyWriteExecute` breaks JIT runtimes; re-check if the runtime changes.
- "active" is not "ready": about 90 ms between systemd's "Started" and the socket being
  bound. Stage 2 adds `/ready` and considers `Type=notify`.
- `/health` reports `0.0.0+source` until the package is installed (Stage 2 virtualenv or
  Stage 3 image).
- The app unit is retired after Stage 3 (Compose); the contract and the backup timer remain.

## Verification (2026-10-26)

| Check | Result |
|---|---|
| Deploy key | `ssh -T` greets the repo; `git push --dry-run` → "marked as read only" |
| Code permissions after clone/pull | `640`/`2750`, no group-writable files, no `__pycache__` |
| Service identity | `regassist`, PPID 1, `_CAP_EFFECTIVE 0`, bound to `127.0.0.1:8000` only |
| Probe as `regassist` in the service's mount namespace | `/tmp`, `/var/tmp`, `/dev/shm` private; `app/`, `/etc` denied; `/home` inaccessible; only `data/` writable |
| Crash (`systemctl kill -s KILL`) | restarted after 2 s, `NRestarts=1` |
| Bad config (`REGASSIST_PORT=abc`) | `failed`, `2/INVALIDARGUMENT`, no restart; found with `journalctl -p err` |
| Egress (same directives, transient unit) | localhost 200; github.com timed out |
| Reboot | started at boot without login; previous boot ends with a graceful SIGTERM stop |
