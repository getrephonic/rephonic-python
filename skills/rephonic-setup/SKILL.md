---
name: rephonic-setup
description: Install the Rephonic CLI and Python SDK, configure authentication with an API key, and verify the setup works. Use when a user wants to get started with Rephonic, needs to install the tool, is getting authentication errors, or has never used the Rephonic CLI before.
---

# Set up Rephonic

Rephonic's API has data on more than 4 million podcasts, including listener estimates, demographics, contacts, transcripts and chart rankings. The `rephonic` command calls that API and prints the JSON response, so you can use it from shell scripts and AI coding agents.

## Install

The CLI ships with the Python package. Any of these installs both the SDK and the `rephonic` command:

```bash
pipx install rephonic         # isolated venv, recommended
uv tool install rephonic      # if you use uv
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

## API version

The CLI and SDK request the latest API version, so you don't need to set one. To choose a version, set `REPHONIC_API_VERSION=1.1` or pass `--api-version 1.1` before the command group (`rephonic --api-version 1.1 podcasts get huberman-lab`). In Python, use `Rephonic(api_version="1.1")`. An unknown version fails with exit code 1 and a `BadRequestError`.

## Verify the key works

```bash
rephonic account quota
```

It should print JSON like `{"usage": 42, "quota": 10000}`. If it fails instead, the exit code and the error type on stderr tell you why:

- Exit code 4 with `"type": "AuthenticationError"` means the environment variable is missing or the key is wrong.
- Exit code 1 with `"type": "BadRequestError"` means the key works but the request is malformed.

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

| Group | What it does |
|---|---|
| `rephonic search` | Searches podcasts and episodes, and suggests search terms |
| `rephonic podcasts` | Looks up a podcast and fetches data about it, e.g. its metadata, people, chart rankings, demographics or contacts |
| `rephonic episodes` | Lists a podcast's episodes, gets one episode, or fetches its transcript |
| `rephonic charts` | Fetches the daily Apple, Spotify and YouTube chart rankings |
| `rephonic common` | Lists reference data for filters, e.g. categories, countries and languages |
| `rephonic account` | Shows your quota and usage |

Run `rephonic --help` to list the groups, and `rephonic <group> --help` to see every command and option in a group.

## Docs

- Main docs: https://rephonic.com/developers
- LLM-friendly reference: https://rephonic.com/llms-full.txt
