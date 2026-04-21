# Development rules for rephonic-python

The **official Python client** for the [Rephonic API](https://rephonic.com/developers). It is a public, open-source, pip-installable package — rules differ from `rephonic-web` / `rephonic-app` because this is a library for external developers.

A thin, hand-written wrapper. No code generation. Every method in `src/rephonic/resources/` maps to one HTTP endpoint on [/developers](https://rephonic.com/developers) or in [/llms-full.txt](https://rephonic.com/llms-full.txt).

## General rules

- NEVER install libraries/packages for me (`pip install`, `uv add`, etc.) — just tell me to do it.
- Don't add useless comments saying what you changed. Err on the side of no comments.
- Always use double quotes for strings.
- Prefer `dict()` over `{}` unless keys contain forbidden characters.
- Empty line at end of file.
- Don't remove my comments, TODOs, print statements, or trailing blank lines.
- Let exceptions bubble up. NEVER use bare `except Exception:` — always specify types.

## Different from rephonic-web / rephonic-app

Because this is a public-facing library:

- **YES, use type hints** on all public methods. Internals (`_`-prefixed) more relaxed but still typed.
- **YES, write docstrings** on every public class and method. Short — explain args and return shape, not implementation.
- **YES, ship `py.typed`** ([PEP 561](https://peps.python.org/pep-0561/)).

## Core principles

1. **Stay thin.** No response parsing, transformation, or validation beyond what the API does. Methods return raw `dict`s.
2. **Match the API shape.** Resource/method layout mirrors URL structure.
3. **Sync + async parity.** Every sync method has an async twin. When you add one, add both.
4. **httpx is the only runtime dependency.** Don't add others without discussion.

## Repository map

```
src/rephonic/
  __init__.py          # public exports (Rephonic, AsyncRephonic, exceptions)
  _client.py           # Rephonic + AsyncRephonic, resource composition
  _base_client.py      # BaseClient + AsyncBaseClient: httpx transport, retries, auth, quote_path
  _exceptions.py       # RephonicError hierarchy
  _version.py          # bumped by /release only
  pagination.py        # iter_pages (sync) + aiter_pages (async)
  py.typed             # PEP 561 marker — empty, do not remove
  resources/
    search.py          # Search + AsyncSearch  — /api/search/*
    podcasts.py        # Podcasts + AsyncPodcasts  — /api/podcasts/<id>/* + /contacts, /social, etc.
    episodes.py        # Episodes + AsyncEpisodes  — /api/episodes/*
    charts.py          # Charts + AsyncCharts
    common.py          # Common + AsyncCommon  — reference data
    account.py         # Account + AsyncAccount  — /api/accounts/*
tests/                 # pytest + respx (no network)
examples/              # runnable scripts — work with REPHONIC_API_KEY set
api.md                 # public method reference (keep in sync with resource docstrings)
```

## Adding a new endpoint

1. Find the right resource group by URL prefix.
2. Add a method on **both** the sync and async class in the same file. Signature rules:
   - Path params as positional args (`podcast_id: str`).
   - Query params as keyword-only (`*, query: str | None = None`).
   - Required query params are not optional.
   - If a shared helper simplifies sync/async parity, extract a private `_foo_params(...)` at the top of the file (see `search.py`).
3. `_base_client` auto-strips `None`s and lowercases booleans — don't do it yourself.
4. For path params interpolated into the URL, use `quote_path(...)` from `_base_client`.
5. Short docstring on the sync method.
6. Sync test in `tests/test_resources.py` + async test in `tests/test_async.py` (both using `respx`).
7. Add a row to `api.md`.

## What NOT to do

- No response wrapping in dataclasses / Pydantic.
- No retry logic in resource methods — it belongs in `_base_client`.
- No global state (no module-level `rephonic.api_key = ...`).
- Don't catch exceptions inside resource methods.
- Don't edit `py.typed` — keep it empty.
- Don't hand-edit `_version.py` outside the release flow.

## Running tests

```bash
uv sync --all-extras      # first time
uv run pytest             # run all tests
uv run ruff check . --fix
uv run ruff format .
uv run mypy src
```

## Releasing

Use the `/release` skill (`.claude/skills/release/SKILL.md`). Local flow: bump version → commit → tag → `uv build` → `uv run twine upload` → push.

## Source of truth

- [rephonic.com/developers](https://rephonic.com/developers) — human-readable API reference
- [rephonic.com/llms-full.txt](https://rephonic.com/llms-full.txt) — LLM-friendly markdown API reference

If the library diverges from the API, the API wins — update the library.
