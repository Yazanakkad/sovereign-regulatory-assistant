# Runbook — Backup and restore (regassist-srv01)

| | |
| --- | --- |
| Scope | `/srv/regassist/data` and `/etc/regassist` (code is restored by `git`, not from backups) |
| Schedule | Daily 02:30 Asia/Riyadh (23:30 UTC); missed runs catch up at next boot |
| RPO | Up to 24 hours |
| Technical RTO | 0.34 s for a full `data/` restore, measured 2026-10-27 (352-byte archive) — excludes time to notice and decide |
| Location | `/var/backups/regassist/` (root only, 0700), newest 7 kept |
| Design | ADR-0011 |

All commands run on the VM over SSH.

## 1. Is the backup healthy?

```bash
systemctl list-timers regassist-backup.timer --no-pager; systemctl --failed --no-pager; journalctl -u regassist-backup -p err --since "2 days ago" -o cat --no-pager
sudo sh -c 'ls -l /var/backups/regassist; cd /var/backups/regassist && sha256sum -c regassist-*.sha256'
```

Healthy: LAST is within 24 h, no failed units, no error lines, every archive `: OK`.

## 2. If a backup run failed

| Exit code | Meaning | Action |
| --- | --- | --- |
| 1 | Backup failed (tool error, missing source, name collision) | Read `cause_exit=`, `line=`, `command=` in the journal; fix; `sudo systemctl start regassist-backup.service` |
| 2 | Bad configuration | Check `Environment=` / drop-ins: `systemctl cat regassist-backup.service` |
| 3 | Another run holds the lock | Wait; check `systemctl status regassist-backup.service` |

A failed run never deletes old archives. After fixing: `sudo systemctl reset-failed regassist-backup.service`.

## 3. Pick and verify an archive

```bash
latest=$(sudo sh -c 'ls -1 /var/backups/regassist/regassist-*.tar.gz' | tail -n 1); echo "$latest"; sudo sh -c "cd /var/backups/regassist && sha256sum -c $(basename "$latest").sha256"
```

If verification fails, do not restore from it. Use the next older archive.
List contents: `sudo tar --list --verbose --gzip --file "$latest"`.

## 4. Restore one file or directory

`--keep-old-files` refuses to overwrite anything that exists. Remove or move the damaged item first.

```bash
sudo tar --extract --gzip --keep-old-files --file "$latest" --directory / srv/regassist/data/<path>
```

Owner and mode are restored from the archive (by user name).

## 5. Full restore of data/

Stop the app first: its sandbox holds a bind mount of the old directory, so a running app would keep writing to the moved copy.

1. `sudo systemctl stop regassist-app`
2. Move aside, never delete: `sudo mv /srv/regassist/data /srv/regassist/data.broken-$(date -u +%Y%m%dT%H%M%SZ)`
3. Verify the archive (section 3).
4. `sudo tar --extract --gzip --file "$latest" --directory / srv/regassist/data`
5. `sudo systemctl start regassist-app`, then `curl -fsS http://127.0.0.1:8000/health` (retry for a second: "active" comes before "ready").
6. Check `sudo stat -c '%a %U:%G %n' /srv/regassist/data` → `750 regassist:regassist`.
7. Delete the moved-aside copy only after the service is confirmed healthy.

## 6. Restore configuration (/etc/regassist)

Same as section 5 with `etc/regassist` as the member and `/etc/regassist` as the directory. Expected: directory `750 root:regassist`, `regassist.env` `640 root:regassist`. Restart the app afterwards.

## 7. Known limitations

- Backups are on the same virtual disk as the data: they do not survive loss of the VHDX (off-VM copy is an open item).
- Archives are not encrypted; protection is file permissions only. They will contain secrets and, from Stage 4a, personal data.
- No push alert yet (Stage 5); failures are visible through section 1 only.
