# Sovereign Regulatory AI Assistant

A bilingual (Arabic/English) assistant that answers questions over Saudi regulatory publications (SAMA, PDPL, SDAIA) with grounded answers and citations validated by code. It is built local-first, then on Kubernetes, then on Azure.

> **Status:** Stage 1 of 8 — Linux and networking. This README describes the target; anything not marked done is planned.

## Goals (v1 milestone)

- Same-language answers to Arabic and English questions.
- Every answer grounded in retrieved source passages, with citations checked by code against the retrieved set.
- An explicit "not found in the provided sources" path instead of guessing.
- Measured quality: retrieval, answer, citation and unsupported-answer metrics on a golden set with a frozen held-out split.
- Security tested: redaction of Saudi personal identifiers, a prompt-injection suite, JWT validation.

## Roadmap

| Stage | Focus | Status |
| --- | --- | --- |
| 1 | Linux and networking: hardened Ubuntu Server VM, SSH, firewall, systemd, Nginx + TLS | In progress |
| 2 | FastAPI service, OAuth 2.0 / JWT via JWKS, CI v1 | Planned |
| 3 | Docker Compose, bilingual ingestion, hybrid retrieval, retrieval baseline | Planned |
| 4a | LangGraph agent, code-validated citations, Vue chat UI | Planned |
| 4b | Redaction, prompt-injection suite, evaluation command — **v1** | Planned |
| 5 | Observability: OpenTelemetry, Tempo, Langfuse, Prometheus, Grafana | Planned |
| 6 | CI/CD with an evaluation quality gate | Planned |
| 7 | Local Kubernetes: Helm, Gateway API, autoscaling, failure drills | Planned |
| 8 | Azure via Terraform: AI Search, Container Apps, Entra ID, Managed Identity | Planned |

## Repository layout

```text
.
├── docs/
│   └── adr/          Architecture Decision Records
├── src/regassist/    Application package
├── tests/            pytest suite
├── PROGRESS.md       Build log and current position
└── pyproject.toml    Project metadata and tool configuration
```

## Development

Requirements: Linux or WSL2, [uv](https://docs.astral.sh/uv/), git.

```bash
uv sync                          # create .venv from uv.lock
uv run pre-commit install        # enable commit-time checks
uv run ruff check .              # lint
uv run ruff format --check .     # formatting
uv run mypy src tests            # strict type check
uv run pytest                    # tests
```

## Architecture decisions

Decisions and their trade-offs are recorded in [`docs/adr/`](docs/adr/README.md).

## Disclaimer

This is an engineering portfolio project, not legal or regulatory advice. Source documents are public publications of their issuers; they are not redistributed in this repository and are fetched from official sources by a download script.
