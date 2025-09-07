# Repository Guidelines

This guide helps contributors work consistently in this repository. Keep changes minimal, focused, and aligned with the structure and commands below.

## Project Structure & Module Organization
- `src/` – application code grouped by feature/domain (e.g., `src/users/`, `src/api/`).
- `tests/` – mirrors `src/` (e.g., `tests/users/test_service.py`).
- `scripts/` – developer utilities (e.g., `scripts/format`, `scripts/lint`).
- `docs/` – concise architecture notes, ADRs, and diagrams.
- `assets/` – static files and sample data.
- If a folder is missing, create it with a minimal README describing its purpose.

## Build, Test, and Development Commands
- Build: `make build` (fallbacks: `npm run build` / `cargo build` / `python -m build`).
- Test: `make test` (or `npm test` / `pytest -q` / `cargo test`).
- Lint: `make lint` (or `eslint .` / `ruff check .`).
- Format: `make fmt` (or `prettier -w .` / `black src tests`).
- Run locally: `make run` (or `npm start` / `python -m src.main`).
- Document project-specific flags in `scripts/` or the `Makefile`.

## Coding Style & Naming Conventions
- 4-space indents; UTF-8; LF; max line length 100.
- Names: `snake_case` files/modules, `PascalCase` classes/types, `lowerCamelCase` vars/functions, `UPPER_SNAKE_CASE` constants.
- Imports: group stdlib, third-party, local; keep deterministic order.
- Tools: Prettier, Black, Ruff, ESLint (configs live in repo root).

## Testing Guidelines
- Frameworks: `pytest` / Jest (as applicable to language).
- Location mirrors `src/`; name tests `test_*.py` or `*.spec.*`.
- Target ≥ 80% coverage; prefer fast, deterministic unit tests.
- Run a single test: `pytest tests/foo/test_bar.py::test_happy_path` or `npm test -- foo/bar.spec.ts`.

## Commit & Pull Request Guidelines
- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
- Subject ≤ 72 chars; imperative mood. Body explains why.
- PRs include description, linked issues (e.g., `Closes #123`), and screenshots for UI changes.
- Ensure lint, tests, and build pass before requesting review.

## Security & Configuration Tips
- Do not commit secrets; use env files like `.env.local` (git-ignored).
- Pin dependencies; run audits (`npm audit` / `pip-audit`).
- Store only non-sensitive sample data under `assets/`.

## Agent-Specific Notes
- Scope: this file applies to the entire repository.
- Make minimal, focused changes; avoid unrelated refactors.
- Follow the structure, style, and commands above when adding files.

