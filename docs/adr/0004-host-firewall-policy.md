# ADR-0004: Host firewall — deny inbound, allow outbound

- **Status:** Accepted
- **Date:** 2026-10-05
- **Stage:** 1

## Context

The VM should expose only what it serves. The Default Switch's NAT is not a security control the VM can rely on. An outbound allowlist would need DNS, NTP, Ubuntu mirrors and, later, GitHub and package registries.

## Decision

- `ufw` enabled at boot: default deny incoming, allow outgoing, routed disabled.
- `22/tcp` with `LIMIT` (rate limiting against repeated connection attempts).
- Logging `low`; blocked packets are read with `sudo journalctl -k -g 'UFW BLOCK'`.
- Each later port is opened explicitly in the step that needs it (`443/tcp` in Step 16).

## Alternatives considered

- **Outbound allowlist** — high maintenance for a lab VM whose dependencies change every stage.
- **Raw nftables** — more powerful but less readable while learning.
- **No host firewall** — no defence in depth.

## Consequences

- **Positive:** minimal inbound surface; blocked traffic is visible in the journal.
- **Negative:** outbound traffic, including exfiltration, is not restricted. Egress control is designed later with Kubernetes NetworkPolicies (Stage 7) and Azure NSGs (Stage 8).
