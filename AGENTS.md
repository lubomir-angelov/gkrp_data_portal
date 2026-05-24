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

## Context Engine (CCE)

This project uses Code Context Engine for intelligent code retrieval and
cross-session memory.

### Searching the codebase

**Use `context_search` instead of reading files directly** when exploring
the codebase, answering questions about code, or understanding how things
work. `context_search` returns the most relevant code chunks with
confidence scores instead of whole files.

When to use `context_search`:
- Answering questions about the codebase ("how does X work?", "where is Y?")
- Exploring structure or architecture
- Finding related code, functions, or patterns

Other tools:
- `expand_chunk` for full source of a compressed result
- `related_context` for what calls/imports a function
- `session_recall` to recall past decisions

### Cross-session memory

Call `session_recall("topic phrase")` before answering non-trivial questions.
Call `record_decision(decision="...", reason="...")` after making choices.
Call `record_code_area(file_path="...", description="...")` after meaningful work.

### Output style

Respond in compressed style. Drop articles (a, an, the) in prose. Use
sentence fragments over full sentences. Use short synonyms (fix not resolve,
check not investigate). Pattern: [thing] [action] [reason]. [next step].
No filler, hedging, pleasantries, trailing summaries, or restating what
the user said. One sentence if one sentence is enough.

When suggesting code changes, show only the changed lines with 3 lines of
context. Never rewrite entire files. Multiple changes in one file: show each
change separately. Never echo back unchanged code the user already has.

Code blocks, file paths, commands, error messages: always written in full.
Security warnings and destructive action confirmations: use full clarity.
