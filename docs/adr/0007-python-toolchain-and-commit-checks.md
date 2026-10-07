# ADR-0007: Python toolchain (uv, Python 3.13) and commit-time checks

- **Status:** Accepted
- **Date:** 2026-10-07
- **Stage:** 1

## Context

Every later stage (API, ingestion, evaluation, CI, containers) needs the same reproducible Python environment. The repository is public (ADR-0006), so secrets must be stopped before a commit exists.

## Decision

- **uv** manages the Python version, the virtual environment, dependencies and `uv.lock`, which is committed.
- **Python 3.13**, installed by uv for this project only; the system Python is untouched.
- **src layout** with the package `regassist`; the version lives only in `pyproject.toml` and is read with `importlib.metadata`.
- **ruff** for lint and format (line length 100; rule sets E, W, F, I, B, UP, S, N, SIM, RUF; `assert` allowed only in tests), **mypy** in strict mode, **pytest**.
- **pre-commit** with pinned revisions of pre-commit-hooks (whitespace, final newline, LF line endings, YAML/TOML validity, merge markers, 500 KB file limit, private keys) and **gitleaks**. ruff and mypy run as local hooks through `uv run`, so their versions come from `uv.lock`.
- `.gitignore` excludes `.env*` (except `.env.example`) and `data/raw/`; `.gitattributes` stores text with LF line endings.
- The gitleaks hook was proven with a canary GitHub token, which it blocked.

## Alternatives considered

- **pip + venv + pip-tools, or Poetry** — several tools or a slower resolver for the same result.
- **black + flake8 + isort** — three tools that ruff replaces.
- **Python 3.12** — already in security-only maintenance.
- **Python 3.14** — newest; wheel coverage for ML and OCR libraries is less certain. Re-evaluated in Stage 3.
- **detect-secrets** — requires maintaining a baseline file.

## Consequences

- **Positive:** one command each for lint, format, types and tests; identical versions locally, in hooks and in CI.
- **Negative:** hooks can be bypassed with `--no-verify`, so CI v1 (Stage 2) repeats every check. Hook revisions are updated deliberately with `pre-commit autoupdate`. The Python version is revisited in Stage 3 when embedding and OCR libraries are chosen.
