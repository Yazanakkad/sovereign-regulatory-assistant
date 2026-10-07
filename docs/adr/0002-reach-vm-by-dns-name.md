# ADR-0002: Reach the VM by DNS name, never by DHCP IP

- **Status:** Accepted
- **Date:** 2026-10-04
- **Stage:** 1

## Context

The VM gets its address by DHCP from the Hyper-V Default Switch, which offers no reservations. During Stage 1 the lease changed from `172.27.51.216` to `172.27.56.52` and SSH broke ("Destination host unreachable" — no ARP reply on the old address). The Default Switch also registers VM names in DNS under `mshome.net`, served by the Windows host.

## Decision

- Always address the VM as `regassist-srv01.mshome.net`.
- SSH client aliases (`ssh regassist`), the TLS certificate SAN (Step 16) and all documentation use the name.
- IP addresses appear only in diagnostic output, never in configuration.

## Alternatives considered

- **Static IP on an internal or external switch** — more host networking configuration (NAT or bridging) for a lab VM.
- **Hosts-file entries** — go stale on the next lease change.

## Consequences

- **Positive:** survives lease changes; matches production practice, where clients depend on names and DNS, not addresses.
- **Negative:** depends on the Windows host's DNS for `mshome.net`. A name-resolution failure looks like a server failure, so DNS diagnosis (`dig`, `resolvectl`) is part of the Stage 1 gate.
