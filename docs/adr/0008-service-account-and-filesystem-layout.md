# ADR-0008: Dedicated service account and /srv/regassist filesystem layout

- **Status:** Accepted
- **Date:** 2026-10-11
- **Related:** ADR-0003 (SSH allow-list), ADR-0006 (code reaches the VM via git)

## Context

From Step 13 the application runs on the VM as a systemd service. A process runs with the
privileges of its user: root can do anything, and `yazan` has `sudo` and holds SSH keys in
`~/.ssh`. Any application bug that allows file writes or code execution (a dependency CVE,
a malicious document, prompt injection reaching a tool) acts with those privileges.

Code reaches the VM through `git clone` by the deploy identity (ADR-0006). Ubuntu's default
umask for users is `0002` (user private groups), so files created by `yazan` are
group-writable by default.

## Decision

1. **Service account `regassist`:** system user (UID < 1000), own group, locked password,
   shell `/usr/sbin/nologin`, home `/nonexistent`, no supplementary groups, no sudo rights.
   It is also outside the sshd `AllowUsers` list (ADR-0003).

2. **Filesystem layout:**

   | Path | Owner:group | Mode | Purpose |
   |---|---|---|---|
   | `/srv/regassist` | `root:root` | `0755` | Container; traversable (code is public) |
   | `/srv/regassist/app` | `yazan:regassist` | `2750` | Code: deploy identity writes, service reads |
   | `/srv/regassist/data` | `regassist:regassist` | `0750` | Runtime state: only the service writes |
   | `/etc/regassist` | `root:regassist` | `0750` | Config and env file (Step 13) |

3. **Setgid on `app/`** so cloned files inherit group `regassist` without a `chown`.

4. **Deploy commands that write `app/` run with `umask 027` in a subshell**; the login umask
   stays `0002`. Result: code is `640`/`750`, readable but not writable by the service group.

5. **Admin access to `data/` and `/etc/regassist` goes through `sudo`**, so it is explicit
   and logged.

6. **Accepted gap at this layer:** the service can write `/tmp`, `/var/tmp` and `/dev/shm`
   (world-writable, sticky). Closed in Step 13 by systemd sandboxing (`PrivateTmp=`,
   `ProtectSystem=strict`, `ReadWritePaths=/srv/regassist/data`).

## Alternatives considered

- **Run as root or as `yazan`:** rejected; a compromise becomes full control of the VM, or
  access to the SSH keys and sudo.
- **Code owned by root, deployed with `sudo`:** slightly stronger, but every `git pull`
  needs sudo on a single-operator dev VM. Rejected for now.
- **Separate deploy user (not `yazan`):** separates admin from deploy; more moving parts.
  Revisit if CI ever deploys to the VM.
- **systemd `DynamicUser=`:** ephemeral UID with strong isolation, but no stable owner for
  data in `/srv` and for the Step 14 backup script. Rejected.
- **`StateDirectory=` (`/var/lib/regassist`) instead of `/srv/regassist/data`:** more
  FHS-conventional for service state; `/srv` kept so one tree holds code and data and
  defines the backup scope. May be revisited in Step 13.
- **Global umask `027` for `yazan`:** rejected; it affects every file, while a scoped umask
  is explicit at the point of deploy.

## Consequences

- A compromised application can write only to `data/` (plus temporary directories until
  Step 13), and cannot modify its own code.
- Deploying without `umask 027` makes code group-writable. Post-deploy check:
  `find /srv/regassist/app -perm -g+w` must print nothing.
- `yazan` needs `sudo` to inspect service data (intended).
- The same model maps to containers and cloud later: `runAsNonRoot` / `fsGroup` /
  `readOnlyRootFilesystem` (Stage 7) and a scoped Managed Identity (Stage 8b).

## Verification (2026-10-11, as `regassist` via `sudo -u`)

| Test | Result |
|---|---|
| Write `data/` | Allowed |
| Write `app/` | Denied |
| Read `app/` | Allowed |
| Write `/etc/regassist` | Denied |
| `yazan` reads `data/` without sudo | Denied |
| Read `/home/yazan` | Denied |
| `sudo -l -U regassist` | Not allowed to run sudo |
| Write `/tmp` | Allowed (accepted gap, see Decision 6) |
