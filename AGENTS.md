# Repository Guidelines

## Project Structure & Module Organization

`app.py` is the macOS application entry point. Core behavior lives in `src/`: market quotes, state transitions, animation, audio, bubbles, and the pet window are separated into focused modules. Tests are under `tests/`. Processed animation frames and audio live in `assets/`; source media is retained in `原始素材/`, preview images in `预览图/`, and asset-processing and market-bridge utilities in `tools/`.

## Build, Test, and Development Commands

Use Python 3.12 and a repository-local environment:

```bash
uv venv --python 3.12 .venv
uv pip install -p .venv/bin/python -r requirements.txt
.venv/bin/python app.py
.venv/bin/python -m unittest discover -s tests
./build_app.sh
```

The final command creates `dist/牛来行情桌宠.app`. The Chinese launcher scripts provide equivalent Finder-friendly workflows on macOS.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and uppercase enum members. Keep UI, data access, and state logic in their existing modules. Add type hints to public APIs and concise docstrings where behavior is non-obvious. No formatter or linter is configured; match nearby code.

## Testing Guidelines

Tests use `unittest`. Name files `test_<module>.py`, classes `Test<Behavior>`, and methods `test_<scenario>`. Add deterministic unit tests for state and parsing changes; avoid live-network dependencies. Run the full suite before submission.

## Commit & Pull Request Guidelines

History does not establish a strict convention. Use short, imperative subjects identifying the affected behavior. Pull requests should explain the change, list verification commands, link relevant GitHub issues, and include screenshots or recordings for visible UI changes. Exclude `.venv/`, `dist/`, logs, and temporary generated files.

## Security & Assets

Keep credentials and private connector data out of Git. Treat `config.json` as user-editable defaults. Character artwork and audio are third-party IP; confirm licensing before redistribution or commercial use.

## Agent skills

### Issue tracker

Track issues and specs in this repository's GitHub Issues. Read `docs/agents/issue-tracker.md` before publishing, fetching, or triaging tickets.

### Triage labels

Use the five canonical triage labels without overrides. Read `docs/agents/triage-labels.md` before applying triage state.

### Domain docs

Use the single-context domain-documentation layout. Read `docs/agents/domain.md` before exploring domain terminology or architectural decisions.
