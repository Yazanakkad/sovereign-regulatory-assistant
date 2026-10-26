# ADR-0011: Local backups — verified tar archives from a sandboxed systemd timer

- Status: Accepted
- Date: 2026-10-27

## Context

The service's state that cannot be recreated is `/srv/regassist/data` (empty placeholder today; Postgres and Qdrant data later) and `/etc/regassist` (configuration, secrets later). Code and unit files are in git (ADR-0006, ADR-0009). There is one VM on one virtual disk. RPO/RTO targets are not yet set by the business; Stage 1b turns them into NFRs.

## Decision

- **Scope:** `srv/regassist/data` and `etc/regassist`, archived with relative paths so restores can target `/` or a scratch directory.
- **Destination:** `/var/backups/regassist`, `root:root 0700`; archives and checksums `0600` (`umask 077`). The service account cannot read, change or delete backups.
- **Script:** `deploy/backup/regassist-backup.sh`, installed as a root-owned copy at `/usr/local/sbin/regassist-backup`. Strict mode; `flock` against concurrent runs; write to a temporary file in the same directory → read the whole archive back → SHA-256 file → atomic rename → `sync`. UTC-stamped names (`regassist-YYYYMMDDTHHMMSSZ.tar.gz`). gzip for portability.
- **Retention:** newest 7, counted, applied only after a verified success, and never pruning the archive just written (protects against clock jumps, ADR-0010).
- **Exit codes:** 0 ok · 1 failed (tool failures mapped to 1, original code logged as `cause_exit`) · 2 bad configuration · 3 locked. Logs are logfmt with syslog priorities.
- **Unit:** `Type=oneshot`, root reduced to `CAP_DAC_READ_SEARCH` (read and traverse only), `ProtectSystem=strict` with one writable path, no network (`PrivateNetwork`, `IPAddressDeny=any`), seccomp `@system-service`, `TimeoutStartSec=30min`, low CPU/IO priority. Exposure 1.3 OK.
- **`RestrictSUIDSGID=` is not set.** Its seccomp filter cannot inspect `openat2()`'s mode, so it answers `openat2()` with ENOSYS; the tar shipped with Ubuntu 26.04 opens directories with `openat2()` and does not fall back. Found by bisecting the sandbox. Compensating controls: `ProtectSystem=strict`, the root-only 0700 destination, `NoNewPrivileges=yes`.
- **Timer:** `OnCalendar=*-*-* 02:30:00 Asia/Riyadh`, `Persistent=true` (catch-up after the laptop was off).
- **Restore:** procedure in `docs/runbooks/backup-restore.md`; verify the checksum before any restore; stop the app for a full restore. Drilled 2026-10-27: single file, full `data/` (technical RTO 0.34 s), corrupted-archive detection.

## Alternatives considered

- **Run as `regassist`:** it can read both sources, but a compromised app could then delete or tamper with its own backups. Rejected.
- **Run as unrestricted root:** works, but grants write override, chown and network to the most privileged reader on the box. Rejected.
- **restic or borg:** deduplication, encryption and remote repositories built in. Better once backups leave the VM; more to learn and operate now. Revisit with the off-VM copy.
- **Age-based retention:** deletes everything if backups silently stop. Rejected for count-based.
- **Hyper-V checkpoints as backups:** tied to the same VM and disk, and not restorable file by file. Kept for lab rollback only.
- **zstd:** faster, but gzip is guaranteed in WSL, CI and minimal containers; one flag to change later.

## Consequences

- Backups are verified at write time and at restore time, made with least privilege, and restorable by a documented, drilled procedure.
- Backups share the VM's disk: no protection against VHDX loss. Off-VM copy is an open item, as a separate unit with network access and read-only access to the archives.
- Archives are unencrypted at rest; file permissions are the only protection. Encryption comes with the off-VM copy.
- No push alerting until Stage 5; failures are visible via `systemctl --failed` and `journalctl -p err`.
- File-level archiving is only consistent while `data/` holds static files. Stage 3 adds application-consistent dumps (Postgres `pg_dump`, Qdrant snapshot API) before archiving.
- From Stage 4a, the personal-data retention period must include backups: a record deleted from Postgres survives in backups for up to 7 days.
- The `tar`/`openat2`/`RestrictSUIDSGID` interaction must be re-tested after `tar` or systemd upgrades.
