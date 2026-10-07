# ADR-0006: Dev workspace in WSL; public GitHub repo as source of truth

- **Status:** Accepted
- **Date:** 2026-10-07
- **Stage:** 1

## Context

Code needs one home that matches the Linux environment of CI and containers. Files on `/mnt/c` are slow to access from WSL and lose Unix permission bits. The VM is the server and should not be edited by hand. GitHub Free provides rulesets and branch protection only on public repositories, and the Stage 6 gate (a bad pull request is blocked automatically) depends on them.

## Decision

- Development happens in WSL Ubuntu 24.04 on the Linux filesystem (`~/code/sovereign-regulatory-assistant`), edited with VS Code through the WSL extension.
- The public repository `Yazanakkad/sovereign-regulatory-assistant` on GitHub is the source of truth. The VM receives code only through git, with a read-only deploy key.
- WSL authenticates to GitHub with a dedicated key (`id_ed25519_github`); the GitHub host key was verified against GitHub's published fingerprints.
- Commits use the GitHub noreply email.

## Alternatives considered

- **Repo under `/mnt/c`** — slow I/O and broken permission bits.
- **Develop on the VM** — mixes the build machine with the server.
- **Private repo** — no rulesets on GitHub Free; would have to be made public before Stage 6.

## Consequences

- **Positive:** the same Linux toolchain locally, in CI and in containers; public commit history is part of the portfolio; per-purpose keys can be revoked independently.
- **Negative:** everything committed is public and permanent. No secrets, personal data or redistributed source PDFs may enter git; ADR-0007 defines the controls.
