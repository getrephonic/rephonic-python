# Rephonic Python

Official Python client for the [Rephonic](https://rephonic.com) podcast API. Covers 3+ million podcasts with listener estimates, demographics, contact details, chart rankings, episodes, full transcripts, and more.

Thin, typed wrapper around the [Rephonic HTTP API](https://rephonic.com/developers). If you want to plug Rephonic into an AI assistant instead, use the [Rephonic MCP Server](https://github.com/getrephonic/rephonic-mcp).

## What you can build with it

- Enrich a CRM with podcast metadata, listener estimates, and contacts
- Filter podcasts by audience demographics, topic, or reach, then pull verified contact emails in one pass (good for guest pitching and media lists)
- Monitor brand mentions by polling `search.episodes` with a rolling `threshold`
- Pull age, gender, education, profession, income, interests, and location breakdowns for any show
- Grab daily Apple, Spotify, and YouTube chart data across countries and categories
- Audit sponsorships: who's advertising on which shows, with ad copy and promo codes extracted from transcripts
- Feed full-text, speaker-labelled transcripts into your own LLM pipeline
- Power a podcast discovery app: search, autocomplete, audience graph, similar podcasts

## Install

```bash
pip install rephonic
```

Python 3.8+.

## Quickstart

Grab an API key from [rephonic.com/developers](https://rephonic.com/developers).

```python
from rephonic import Rephonic

client = Rephonic(api_key="your_api_key")

# Look up a podcast
podcast = client.podcasts.get("huberman-lab")
print(podcast["podcast"]["name"], podcast["podcast"]["downloads_per_episode"])

# Search for podcasts with filters
results = client.search.podcasts(
    query="artificial intelligence",
    filters="listeners:gte:10000,active:is:true",
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

`AsyncRephonic` has the same surface but returns coroutines. Useful when you want to fan out many calls concurrently (enrichment pipelines, media lists, realtime monitoring).

```python
import asyncio
from rephonic import AsyncRephonic

async def main():
    async with AsyncRephonic(api_key="your_api_key") as client:
        podcast = await client.podcasts.get("huberman-lab")

        # These run concurrently.
        podcast_ids = ["huberman-lab", "the-daily", "lex-fridman-podcast"]
        contacts = await asyncio.gather(
            *(client.podcasts.contacts(pid) for pid in podcast_ids)
        )

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
| `client.podcasts` | `get`, `people`, `demographics`, `promotions`, `contacts`, `social`, `feedback`, `reviews`, `trends`, `similar_graph` |
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

Search endpoints accept a `filters` string with comma-separated `field:operator:value` clauses:

```python
client.search.podcasts(
    query="marketing",
    filters=(
        "listeners:gte:5000,"
        "active:is:true,"
        "categories:any:1482-1406,"
        "locations:any:us,"
        "professions:any:Doctor-Lawyer"
    ),
)
```

Full list of filters and operators at [rephonic.com/developers/search-filters](https://rephonic.com/developers/search-filters). Use `client.common.categories()`, `countries()`, `languages()`, `sponsors()`, `professions()`, and `interests()` to look up valid IDs.

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

The `$299/month` plan includes 10,000 requests per month. Check current usage with:

```python
client.account.quota()
# {"usage": 292, "quota": 10000}
```

See [rephonic.com/developers](https://rephonic.com/developers#pricing) for plan details or [contact us](https://rephonic.com/contact) for higher volume.

## Related resources

- [Rephonic API docs](https://rephonic.com/developers)
- [Markdown API reference for LLMs](https://rephonic.com/llms-full.txt) (feed to any model to generate integration code)
- [Rephonic MCP Server](https://github.com/getrephonic/rephonic-mcp) for Claude, ChatGPT, and Cursor
- [rephonic.com](https://rephonic.com)

## License

[MIT](./LICENSE)
