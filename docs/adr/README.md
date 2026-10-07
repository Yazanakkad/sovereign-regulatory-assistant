# Architecture Decision Records

Each significant decision is recorded as a short ADR: the context, the decision, the alternatives considered and the consequences. ADRs are never edited to change a decision; a new ADR supersedes the old one.

New ADR: copy [`template.md`](template.md) to `NNNN-short-title.md` with the next number.

| ADR | Title | Status |
| --- | --- | --- |
| [0001](0001-hyper-v-ubuntu-server-vm.md) | Hyper-V Gen2 Ubuntu Server VM as the server | Accepted |
| [0002](0002-reach-vm-by-dns-name.md) | Reach the VM by DNS name, never by DHCP IP | Accepted |
| [0003](0003-ssh-keys-only-hardening.md) | SSH: ed25519 keys only, hardening via drop-in | Accepted |
| [0004](0004-host-firewall-policy.md) | Host firewall: deny inbound, allow outbound | Accepted |
| [0005](0005-wsl-to-vm-forwarding.md) | WSL to VM via IPv4 forwarding on vEthernet adapters | Accepted (automation open) |
| [0006](0006-dev-workspace-and-public-repo.md) | Dev workspace in WSL; public GitHub repo as source of truth | Accepted |
| [0007](0007-python-toolchain-and-commit-checks.md) | Python toolchain (uv, 3.13) and commit-time checks | Accepted |
