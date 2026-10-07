# ADR-0003: SSH — ed25519 keys only, hardening via drop-in

- **Status:** Accepted
- **Date:** 2026-10-04
- **Stage:** 1

## Context

SSH is the only administrative path to the VM. Password authentication invites brute force; root login removes accountability; editing the packaged `sshd_config` directly conflicts with package upgrades. Ubuntu ships `50-cloud-init.conf`, which enables password authentication.

## Decision

- Authentication: ed25519 keys with a passphrase, one key per client — Windows (`id_ed25519_regassist`, held by the Windows ssh-agent) and WSL (`id_ed25519_regassist_wsl`). Client configs set `IdentitiesOnly yes`.
- Server hardening in `/etc/ssh/sshd_config.d/10-hardening.conf`: `PasswordAuthentication no`, `PermitRootLogin no`, `AllowUsers yazan`, `MaxAuthTries 3`, `X11Forwarding no`. The `10-` prefix wins over `50-cloud-init.conf` because sshd takes the first value it reads; the effective result is verified with `sshd -T`.
- The server host key fingerprint (`SHA256:GqrCzbHA3iwDOCyHn8h/dQyEvRePV1k44z8VlGsXs2Q`) was verified out of band before first trust.
- Least privilege: `yazan` removed from the `lxd` group, which is root-equivalent without sudo or audit logs.

## Alternatives considered

- **Passwords plus fail2ban** — reduces but does not remove the brute-force surface.
- **RSA keys** — larger and slower with no benefit here.
- **Editing `sshd_config` in place** — overwritten or conflicted by package upgrades.

## Consequences

- **Positive:** no password attack surface; each client key can be revoked independently; configuration survives upgrades.
- **Negative:** losing both client keys means recovery through the Hyper-V console, which cannot paste. Checkpoints before risky changes mitigate this.
