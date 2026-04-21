---
name: rephonic-setup
description: Install the Rephonic CLI and Python SDK, configure authentication with an API key, and verify the setup works. Use when a user wants to get started with Rephonic, needs to install the tool, is getting authentication errors, or has never used the Rephonic CLI before.
---

# Set up Rephonic

Rephonic is a podcast intelligence API covering 3M+ podcasts with listener estimates, demographics, contacts, transcripts, and chart rankings. The `rephonic` CLI wraps the HTTP API for shell use and AI coding agents.

## Install

The CLI ships with the Python package. Any of these installs both the SDK and the `rephonic` command:

```bash
pipx install rephonic         # isolated venv, recommended
uv tool install rephonic      # modern alternative
pip install rephonic          # if already in a Python project
```

Verify:

```bash
rephonic --version
```

## Authenticate

Get an API key at https://rephonic.com/developers. Set it in the environment:

```bash
export REPHONIC_API_KEY=your_key_here
```

All commands read this env var. There is no config file and no `login` subcommand.

## Verify the key works

```bash
rephonic account quota
```

Should print JSON like `{"usage": 42, "quota": 10000}`. If you get:

- Exit code 4 with `"type": "AuthenticationError"` on stderr: env var missing or key is wrong.
- Exit code 1 with `"type": "BadRequestError"`: key works but the request is malformed.

## Output format

Every command writes JSON to stdout. Pipe through `jq` to extract fields:

```bash
rephonic podcasts get huberman-lab | jq '.podcast.name'
```

Errors go to stderr as structured JSON:

```json
{"error": {"type": "AuthenticationError", "message": "...", "status_code": 401}}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | API or network error |
| 2 | Usage error (bad flags) |
| 4 | Authentication error |
| 5 | Server error (5xx) |

## Command groups

- `rephonic search` — search podcasts and episodes
- `rephonic podcasts` — metadata, people, demographics, contacts, trends
- `rephonic episodes` — list, get, transcript
- `rephonic charts` — Apple, Spotify, YouTube daily rankings
- `rephonic common` — reference data (categories, countries, languages, etc.)
- `rephonic account` — quota

Run `rephonic --help` and `rephonic <group> --help` for the full surface.

## Docs

- Main docs: https://rephonic.com/developers
- LLM-friendly reference: https://rephonic.com/llms-full.txt
