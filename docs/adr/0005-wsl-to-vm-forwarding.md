# ADR-0005: WSL to VM via IPv4 forwarding on the vEthernet adapters

- **Status:** Accepted (automation open)
- **Date:** 2026-10-05
- **Stage:** 1

## Context

WSL2 and the Default Switch are separate Hyper-V virtual networks. Traffic from WSL to the VM was dropped until the Windows host was allowed to route between them. With forwarding on, the VM sees WSL's own address (`172.21.48.20` at the time): the traffic is routed, not NATed.

## Decision

Enable IPv4 forwarding on both adapters from an Admin PowerShell:

```powershell
Set-NetIPInterface -InterfaceAlias "vEthernet (WSL (Hyper-V firewall))","vEthernet (Default Switch)" -AddressFamily IPv4 -Forwarding Enabled
```

The setting resets after a Windows reboot or a WSL restart and is re-applied manually until automated.

## Alternatives considered

- **WSL mirrored networking mode** — changes WSL's whole network model and may affect Docker Desktop from Stage 3; untested.
- **Windows client only** — loses WSL as the Linux-native client used from Stage 3 onward.
- **`netsh interface portproxy`** — one rule per port; hides the real source address.

## Consequences

- **Positive:** both clients reach the VM; the VM logs the real client address.
- **Negative:** a manual step after every reboot until automated (candidate: a scheduled task at logon). The Windows host routes between the two networks, so the VM's default-deny firewall (ADR-0004) remains essential.
