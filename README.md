# rephonic-python

This is the official Python client for the [Rephonic](https://rephonic.com) API. Rephonic has data on more than 4 million podcasts, including listener estimates, audience demographics, contact details, chart rankings, episodes and transcripts.

The client is a small, typed wrapper around the [Rephonic HTTP API](https://rephonic.com/developers), and each method returns the API's JSON response as a plain dict. Installing it also gives you a [`rephonic` command](#command-line) that you can call from shell scripts or hand to an AI coding agent. To use Rephonic inside an AI assistant over the Model Context Protocol, use the [Rephonic MCP Server](https://github.com/getrephonic/rephonic-mcp) instead.

## Examples of what you can do

- Search for podcasts with `search.podcasts`, using `filters` to narrow the results, e.g. to active shows with at least 5,000 listeners per episode. Then fetch each show's email contacts with `podcasts.contacts`.
- Monitor brand mentions by polling `search.episodes` with a rolling `threshold`.
- Get a show's estimated listener demographics, e.g. age, profession or location, with `podcasts.demographics`.
- Fetch the daily Apple, Spotify or YouTube chart for a country and category with `charts.rankings`.
- See which sponsors advertise on a show, along with their ad text and promo codes, with `podcasts.promotions`.
- Download an episode's transcript with `episodes.transcript`. It comes as timestamped segments with speaker labels.

## Install

```bash
pip install rephonic            # SDK (and CLI)
pipx install rephonic           # CLI in an isolated venv (recommended for the CLI)
```

Python 3.8+.

## Command line

`pip install rephonic` also installs a `rephonic` command. Every method on the Python client has a CLI equivalent. It reads your API key from `REPHONIC_API_KEY` in the environment. Results are printed to stdout as JSON, and errors are printed to stderr as JSON.

```bash
export REPHONIC_API_KEY=your_api_key

# Look up a podcast
rephonic podcasts get huberman-lab | jq '.podcast.name'

# Search with filters
rephonic search podcasts \
  --query "marketing" \
  --filters '{"listeners":{"gte":10000},"active":true}'

# Fetch an episode's transcript
rephonic episodes transcript kzaca-huberman-lab-dr-brian-keating-charting-the-a \
  | jq '.transcript.segments[].text'

# Where it ranks in the Apple, Spotify, and YouTube charts
rephonic podcasts rankings huberman-lab

# Check your quota
rephonic account quota
```

Exit codes: `0` success, `1` API or network error, `2` usage error (bad flags), `4` authentication error, `5` server error (5xx).

Run `rephonic --help` for the full command tree, or `rephonic <group> --help` (e.g. `rephonic podcasts --help`) for commands inside a group. The six groups match the Python client: `search`, `podcasts`, `episodes`, `charts`, `common`, `account`.

### Agent skills

The repo also ships [Agent Skills](https://agentskills.io/) for common workflows (setup, search with filters, contact enrichment, similar-podcast discovery, transcript pulls). Install them into your agent's skills directory with the [`skills`](https://skills.sh) CLI:

```bash
npx skills add getrephonic/rephonic-python
```

The `skills` CLI finds the agents you have installed. It supports Claude Code, Cursor, Copilot, Gemini CLI, Goose and about 40 others.

## Python quickstart

Get an API key from [rephonic.com/developers](https://rephonic.com/developers).

```python
from rephonic import Rephonic

client = Rephonic(api_key="your_api_key")

# Look up a podcast by its Rephonic slug
podcast = client.podcasts.get("huberman-lab")
print(podcast["podcast"]["name"], podcast["podcast"]["downloads_per_episode"])

# ... or by an external identifier (Apple, Spotify, YouTube, RSS)
match = client.podcasts.lookup(itunes_id=1545953110)
slug = match["podcasts"][0]["id"] if match["podcasts"] else None

# Search for podcasts with filters
results = client.search.podcasts(
    query="artificial intelligence",
    filters={"listeners": {"gte": 10000}, "active": True},
    per_page=25,
)
for p in results["podcasts"]:
    print(p["id"], p["name"])

# Get a full transcript
transcript = client.episodes.transcript("kzaca-huberman-lab-dr-brian-keating-charting-the-a")
for segment in transcript["transcript"]["segments"]:
    print(segment["text"])
```

The client also picks up `REPHONIC_API_KEY` from the environment:

```python
import os
os.environ["REPHONIC_API_KEY"] = "your_api_key"

from rephonic import Rephonic
client = Rephonic()
```

Use it as a context manager to release the HTTP connection pool when you're done:

```python
with Rephonic() as client:
    quota = client.account.quota()
```

## Async

`AsyncRephonic` has the same methods as `Rephonic`, but each one returns a coroutine.

```python
import asyncio
from rephonic import AsyncRephonic

async def main():
    async with AsyncRephonic(api_key="your_api_key") as client:
        podcast = await client.podcasts.get("huberman-lab")

        # Auto-paginating async iterator.
        async for p in client.search.iter_podcasts(query="ai", limit=500):
            print(p["name"])

asyncio.run(main())
```

## Resources

The API is organised into six resource groups on the client. For the full method reference see [api.md](./api.md).

| Resource | Methods |
|---|---|
| `client.search` | `podcasts`, `iter_podcasts`, `episodes`, `iter_episodes`, `autocomplete` |
| `client.podcasts` | `lookup`, `get`, `people`, `rankings`, `demographics`, `promotions`, `contacts`, `social`, `feedback`, `reviews`, `trends`, `similar_graph` |
| `client.episodes` | `list`, `iter_list`, `get`, `transcript` |
| `client.charts` | `index`, `rankings` |
| `client.common` | `categories`, `countries`, `languages`, `sponsors`, `professions`, `interests` |
| `client.account` | `quota` |

## Pagination

Search endpoints and `episodes.list` return one page at a time. Each resource also exposes an `iter_*` helper that fetches subsequent pages for you:

```python
# Manual paging
page1 = client.search.podcasts(query="ai", per_page=50, page=1)
page2 = client.search.podcasts(query="ai", per_page=50, page=2)

# Auto-paging
for podcast in client.search.iter_podcasts(query="ai", limit=500):
    print(podcast["name"])
```

## Error handling

Every non-2xx response is raised as a subclass of `RephonicError`:

```python
from rephonic import (
    Rephonic,
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    InternalServerError,
)

client = Rephonic()

try:
    client.podcasts.get("does-not-exist")
except BadRequestError as exc:
    # Rephonic returns 400 for missing resources too, so inspect exc.message.
    print(exc.status_code, exc.message)
except RateLimitError:
    # Back off and retry later.
    ...
except APIConnectionError:
    # Network-level problem (DNS, timeout, TLS).
    ...
```

> The Rephonic API returns `400 Bad Request` for missing resources, not 404. Catch `BadRequestError` and check `.message` (e.g. `"Podcast not found."`, `"Unknown episode."`) to distinguish them.

The client retries automatically on 429 and 5xx responses with exponential backoff (`max_retries=2` by default). Pass `max_retries=0` to disable.

## Filters

Pass `filters` as a dict with one key per field. How you write each value depends on the field:

- A boolean field takes `True` or `False`.
- A numeric field takes `gte` (at least) and `lte` (at most).
- A field with several values takes `any` or `in`. `any` matches podcasts that have at least one of the listed values. `in` matches only podcasts that have every listed value, so it works differently from SQL's `IN`.

```python
client.search.podcasts(
    query="marketing",
    filters={
        "listeners": {"gte": 5000},
        "active": True,
        "categories": {"any": [1482, 1406]},
        "locations": {"any": ["us"]},
        "professions": {"any": ["Doctor", "Lawyer"]},
        "founded": {"gte": 1517270400, "lte": 1589932800},
    },
)
```

In the dict form, the client escapes the reserved characters `-`, `,`, `:` and `\` inside values for you, so you can pass a value such as `"Harley-Davidson"` unchanged.

Full list of filters and operators at [rephonic.com/developers/search-filters](https://rephonic.com/developers/search-filters). Use `client.common.categories()`, `countries()`, `languages()`, `sponsors()`, `professions()`, and `interests()` to look up valid values.

Other accepted shapes for `filters`:

```python
# List of raw clauses
filters=["listeners:gte:5000", "active:is:true"]

# Legacy comma-separated string (still supported)
filters="listeners:gte:5000,active:is:true"
```

## API versions

The client and CLI send the latest API version (`1.1`) in the `X-Rephonic-Api-Version` header on every request. To choose a version, pass it to the client:

```python
client = Rephonic(api_version="1.1")
```

or set `REPHONIC_API_VERSION=1.1` in the environment. In the CLI, pass `--api-version 1.1` before the command group, e.g. `rephonic --api-version 1.1 podcasts get huberman-lab`. The constructor argument and the flag win over the environment variable. An unknown version raises `BadRequestError` with the API's message.

## Advanced configuration

```python
import httpx
from rephonic import Rephonic, AsyncRephonic

client = Rephonic(
    api_key="...",
    timeout=60.0,
    max_retries=3,
    # Bring your own httpx.Client for proxies, mTLS, custom transports.
    http_client=httpx.Client(
        proxies="http://corp-proxy:8080",
        verify="/path/to/custom-ca.pem",
    ),
)

# For async, pass an httpx.AsyncClient.
async_client = AsyncRephonic(
    api_key="...",
    http_client=httpx.AsyncClient(proxies="http://corp-proxy:8080"),
)
```

## Rate limits and quota

Check your current monthly usage:

```python
client.account.quota()
# {"usage": 292, "quota": 10000}
```

See [rephonic.com/developers](https://rephonic.com/developers#pricing) for plan details or [contact us](https://rephonic.com/contact) for higher volume.

## Related resources

- [Rephonic API docs](https://rephonic.com/developers)
- [Markdown API reference for LLMs](https://rephonic.com/llms-full.txt), which you can give to a model when you ask it to write integration code
- [Rephonic MCP Server](https://github.com/getrephonic/rephonic-mcp) for Claude, ChatGPT, and Cursor
- [rephonic.com](https://rephonic.com)

## License

[MIT](./LICENSE)
