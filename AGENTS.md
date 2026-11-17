# Xây Dựng Số — Agent Instructions

## Project

Windows-first, local-first, single-user desktop application. Current development scope: **Dashboard, record management, reminders and one-way Excel export** following the approved module specifications. Foundation is implemented.

## Stack

Python 3.12 · PyQt6 · PyQt6-Fluent-Widgets · SQLite · uv · pytest · Ruff.

## Non-negotiable rules

- Read `docs/README.md` and only the documents relevant to the requested task.
- Implement only approved scope; do not invent unresolved business rules.
- Follow Modular Monolith and Layered Architecture, pragmatically.
- Apply KISS, YAGNI, DRY and Ponytail-style minimal-change principles, without sacrificing correctness.
- Use `uv` for Python package/environment management; commit `uv.lock`.
- Keep domain logic independent of UI, database drivers and document libraries.
- SQLite is the authoritative data store; Excel is **one-way generated output** using `docs/modules/excel/templates/so_theo_doi.xlsx`.
- Do not implement Excel-to-SQLite import/sync, cloud integration, or database backup/restore.
- Approved record statuses: `Chưa hoàn thành`, `Đã hoàn thành`.
- Deletion means permanent deletion; no soft-delete flag.
- Preserve the approved Excel template byte-for-byte during normal exports.
- Do not modify unrelated files or automatically commit/push.

## Document routing

- Architecture → `docs/architecture/`
- Development conventions → `docs/development/`
- Fluent UI → `docs/ui/design-guidelines.md`
- Dashboard → `docs/modules/dashboard/`
- CPXD workflow → `docs/modules/cpxd/`
- SQLite → Excel export → `docs/modules/excel/`
- Reminders → `docs/modules/reminders/`
- Phase scope → `docs/roadmap/`

## Workflow

1. Inspect repository state, relevant code, and pertinent documentation.
2. Plan the smallest complete change; identify unresolved requirements.
3. Implement only the requested feature/phase.
4. Run relevant checks (when configured):

   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```

5. Report changed files, verification and limitations. Never claim unexecuted tests passed.

## Current restrictions

Word generation and construction-specific calculations remain deferred until their templates and rules are approved. Do not reinterpret historical Phase 01.1 restrictions as blocking the now-approved record-management scope. See `docs/roadmap/overview.md`, the module specifications and `process.md` for the current implementation handoff. Native Windows packaging and notification behavior must be verified on Windows before claiming acceptance.
