# ADR-0001: Hyper-V Gen2 Ubuntu Server VM as the server

- **Status:** Accepted
- **Date:** 2026-10-04
- **Stage:** 1

## Context

Stage 1 needs a real Linux server to learn systemd, SSH, firewalling, Nginx and TLS. The host is a Windows 11 Pro laptop (i7-1355U, 40 GB RAM, integrated GPU). WSL2 already provides Linux, but it is a development environment with Windows-managed networking, not a representative server. Local work must cost $0; cloud spend is reserved for the Stage 8 credit window.

## Decision

- Server: Hyper-V Generation 2 VM `regassist-srv01` — 2 vCPU, 4 GB fixed RAM, 40 GB VHDX, Secure Boot with the `MicrosoftUEFICertificateAuthority` template, automatic checkpoints off.
- OS: Ubuntu Server 26.04.1 LTS on LVM, ISO verified against `SHA256SUMS` before install.
- Clients: Windows OpenSSH and WSL Ubuntu 24.04. All administration is done over SSH, not the Hyper-V console.

## Alternatives considered

- **VirtualBox or VMware Workstation** — type 2 hypervisors that must coexist with the Hyper-V platform WSL2 already uses; extra software for no gain.
- **WSL2 only** — no real server boundary; would hide the networking, firewall and service-management problems Stage 1 exists to teach.
- **A cloud VM** — costs money outside the planned Azure window.

## Consequences

- **Positive:** a type 1 hypervisor that is already enabled; a real network boundary between client and server; checkpoints for quick rollback.
- **Negative:** 4 GB of host RAM is reserved while the VM runs. Checkpoints are not backups (Step 14 adds a real backup). The Default Switch brings changing DHCP addresses (ADR-0002) and isolation from WSL (ADR-0005).
