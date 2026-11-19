# Xây Dựng Số — Claude Code Instructions

**Windows-only** (10/11), local-first, single-user desktop app (no Linux/macOS code paths): **Dashboard, record management, reminders
and one-way Excel export** per the approved specifications in `.claude/docs/`.
Stack: Python 3.12 · PyQt6 · PyQt6-Fluent-Widgets · SQLite · uv · pytest · Ruff.

## Non-negotiable rules

- Read `.claude/docs/README.md` and only the documents relevant to the task.
- Implement only approved scope; do not invent unresolved business rules.
- Modular Monolith, layered (presentation / application / domain / infrastructure / core),
  pragmatically. KISS, YAGNI, DRY, minimal change — without sacrificing correctness.
- Use `uv` for packages/environments; commit `uv.lock`.
- Keep domain logic independent of UI, database drivers and document libraries.
- SQLite is the authoritative store. Write one-way into a user-selected existing workbook with the
  approved 14-column layout (A–N, no STT) of `docs/modules/excel/templates/so_theo_doi.xlsx`; the
  user chose that file itself as the working file. One Excel setting, merge by record code, update
  in place preserving layout and unrelated rows/parts; never recreate it from an empty template
  and no replace-all mode.
- Never: Excel → SQLite import/sync, cloud integration, database backup/restore.
- Record statuses: `Chưa hoàn thành`, `Đã hoàn thành`. Deletion is permanent (no soft delete).
- Record CRUD never creates or edits reminders; Reminders owns scheduling (absolute deadline minus
  a user-selected lead interval). Excel has no reminder-time column.
- Do not modify unrelated files; never commit or push automatically.

## Document routing (`.claude/docs/`, one file per topic)

| Topic | File |
|---|---|
| Architecture, conventions, testing | `architecture.md` |
| UI, typography, icons, logo | `ui.md` |
| Dashboard | `dashboard.md` |
| Records (CPXD) and SQLite schema | `records.md` |
| SQLite → Excel export | `excel.md` |
| Reminders and notification templates | `reminders.md` |
| Settings | `settings.md` |
| Index, maintenance rules, roadmap/scope | `README.md` |

Superseded decisions and verification status: end of `.claude/docs/README.md` — do not revert
them because of older history. Session log/handoff: `.claude/process.md`.

## Workflow

1. Inspect repository state, relevant code and documentation.
2. Plan the smallest complete change; identify unresolved requirements.
3. Implement only the requested feature.
4. Run checks: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`
5. Report changed files, verification and limitations; never claim unexecuted tests passed.
   Update `.claude/docs/` and `.claude/process.md` with behaviour changes.

## Current restrictions

Word generation and construction-specific calculations stay deferred until their templates and
rules are approved. Native Windows packaging and notification behaviour must be verified on
Windows before claiming acceptance.
