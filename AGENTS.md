# gkrp_data_portal Agent Rules

This is a Python web/data application using NiceGUI, FastAPI-style service structure, SQLAlchemy 2.0 ORM, Alembic, PostgreSQL, Plotly, pytest, ruff, Docker Compose, and Makefiles.

## Working style

- Make small, targeted changes.
- Inspect existing code before editing.
- Prefer modifying existing modules over introducing new abstractions.
- Keep UI logic, repository/query logic, and shared analytics config decoupled.
- Do not rewrite large files unless explicitly requested.
- Do not change database schema without explaining the Alembic migration impact.
- Do not run destructive commands such as `git reset`, `git clean`, `docker compose down -v`, or DB reset targets.

## Python standards

- Use Python built-ins and existing project dependencies.
- Follow PEP 8 and project conventions.
- Use Google-style docstrings when adding public functions/classes.
- Keep type hints precise.
- Prefer explicit dataclasses or typed dictionaries where they clarify boundaries.
- Use structured logging where the project already logs diagnostics.

## gkrp_data_portal architecture notes

- UI pages live under the NiceGUI page layer.
- Analytics query construction belongs in the analytics repository/common modules, not directly inside page rendering code.
- Analytics result columns use prefixes:
  - `l_` for layers
  - `f_` for fragments
  - `o_` for ornaments
  - `fi_` for finds
- Do not reintroduce hidden/non-displayable analytics columns into UI selectors.
- Keep chart fetch limits and table display limits independent.
- Be careful with NiceGUI refresh/update patterns; do not assume normal browser DOM patterns always apply.
- For Plotly/NiceGUI chart updates, preserve explicit update/resize handling where already present.

## Verification

Prefer these checks when relevant:

```bash
ruff check .
ruff format --check .
python -m pytest
python -m compileall src
git diff
```
