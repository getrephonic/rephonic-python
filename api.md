# API Reference

Full method-by-method reference for the Rephonic Python client. For the underlying HTTP endpoints, see [rephonic.com/developers](https://rephonic.com/developers).

All methods return `Dict[str, Any]` matching the raw JSON response from the API.

Every method documented below has an **async counterpart** on `AsyncRephonic` with an identical signature — just `await` the call. `iter_*` methods return async iterators when used on `AsyncRephonic` (use `async for ... in ...`).

---

## `Rephonic(api_key=None, *, base_url=..., timeout=30.0, max_retries=2, http_client=None)`

Synchronous client. Falls back to `REPHONIC_API_KEY` if `api_key` is omitted. Raises `ValueError` if neither is set. Supports use as a context manager (`with Rephonic() as client: ...`).

## `AsyncRephonic(api_key=None, *, base_url=..., timeout=30.0, max_retries=2, http_client=None)`

Async client. Same constructor and resource attributes as `Rephonic`, but every method is a coroutine. Use with `async with AsyncRephonic() as client: ...`. Takes an `httpx.AsyncClient` for `http_client`.

---

## `client.search`

### `search.podcasts(*, query=None, mode=None, per_page=None, page=None, filters=None)`

`GET /api/search/podcasts/`. Search by topic (default), title, or publisher. `filters` accepts a Stripe-style dict (`{"listeners": {"gte": 5000}, "active": True, "categories": {"any": [1482, 1406]}}`), a list of raw clauses (`["listeners:gte:5000"]`), or a legacy comma-separated string. See the [Filters section in the README](./README.md#filters).

### `search.iter_podcasts(*, query=None, mode=None, filters=None, per_page=50, limit=None)`

Iterator over every matching podcast across pages. Stops at `limit` if given.

### `search.episodes(*, query=None, per_page=None, page=None, filters=None, highlight=None, podcast_id=None, threshold=None)`

`GET /api/search/episodes/` — Full-text search across episode titles, show notes, and transcripts. Pass `threshold=N` (seconds, max 1,209,600) to restrict to recent episodes for near-realtime monitoring.

### `search.iter_episodes(*, query=None, filters=None, highlight=None, podcast_id=None, threshold=None, per_page=50, limit=None)`

Iterator over every matching episode.

### `search.autocomplete(*, mode, query)`

`GET /api/search/autocomplete/` — Suggest keywords and matching podcasts. `mode` is one of `topics`, `titles`, `publishers`, `episodes`.

---

## `client.podcasts`

### `podcasts.lookup(*, itunes_id=None, feed_url=None, spotify_id=None, youtube_channel_id=None)`

`GET /api/podcasts/lookup/` — Resolve a podcast from an external identifier. Pass exactly one of the four arguments. Returns `{"podcasts": [...]}` — empty when no match; may contain multiple entries when a `feed_url` or `youtube_channel_id` is shared. Use the returned `id` with the other `podcasts.*` methods.

### `podcasts.get(podcast_id)`

`GET /api/podcasts/<id>/` — Full metadata, chart rankings, YouTube channel, similar podcasts, and latest episode.

### `podcasts.people(podcast_id)`

`GET /api/podcasts/<id>/people/` — Hosts and recent guests with contacts, social accounts, and per-episode details.

### `podcasts.demographics(podcast_id)`

`GET /api/podcasts/<id>/demographics/` — Estimated age, gender, education, profession, income, interests, parenting, relationship status, and country breakdown of listeners.

### `podcasts.promotions(podcast_id)`

`GET /api/podcasts/<id>/promotions/` — Sponsors and cross-promotions with ad text, promo codes, and URLs.

### `podcasts.contacts(podcast_id)`

`GET /api/contacts/` — Email contacts (with `concierge`, `warning`, `upvotes`, `downvotes` quality fields), contact pages, and social accounts.

### `podcasts.social(podcast_id)`

`GET /api/social/accounts/` — Social media accounts with follower and engagement metrics. Channels: `instagram`, `facebook`, `twitter`, `patreon`, `tiktok`, `soundcloud`, `pinterest`, `linkedin_profile`, `linkedin_group`, `clubhouse_club`.

### `podcasts.feedback(podcast_id)`

`GET /api/feedback/` — Overall ratings across apps plus AI-generated summary insights.

### `podcasts.reviews(podcast_id, *, platform)`

`GET /api/reviews/` — Individual listener reviews. `platform` is one of `all`, `apple`, `podchaser`, `castbox`, `audible`, `podaddict`.

### `podcasts.trends(podcast_ids, *, metrics)`

`GET /api/trends/` — Historical time series for metrics. `podcast_ids` accepts a single ID or an iterable (max 3). `metrics` accepts a single metric or iterable (max 5). Allowed metrics: `downloads_per_episode`, `social_reach`, `spotify_followers`.

### `podcasts.similar_graph(podcast_id)`

`GET /api/similar/graph/` — Shared-audience graph (`nodes` + `links`) of podcasts with overlapping listeners.

---

## `client.episodes`

### `episodes.list(*, podcast_id, query=None, per_page=None, page=None)`

`GET /api/episodes/` — Every episode for a podcast in chronological order.

### `episodes.iter_list(*, podcast_id, query=None, per_page=25, limit=None)`

Iterator over every episode across pages.

### `episodes.get(episode_id)`

`GET /api/episodes/<id>/` — Full episode metadata including topics, guests, hosts, sponsors, key moments, Q&A extracts, tone, locations, and safety tags.

### `episodes.transcript(episode_id)`

`GET /api/episodes/<id>/transcript/` — Timestamped transcript segments with speaker IDs and a speaker name mapping where detected.

---

## `client.charts`

### `charts.index(platform)`

`GET /api/charts/<platform>/` — Available countries and categories for one of `apple`, `spotify`, `youtube`.

### `charts.rankings(platform, *, country, category)`

`GET /api/charts/<platform>/<country>/<category>/` — Latest rankings (updated every 24 hours). Use `category="all"` for the overall top chart.

---

## `client.common`

Reference data used with the `filters` parameter on search endpoints.

### `common.categories()` — `GET /api/common/categories/`
### `common.countries()` — `GET /api/common/countries/`
### `common.languages()` — `GET /api/common/languages/`
### `common.sponsors(*, query=None)` — `GET /api/common/sponsors/`
### `common.professions(*, query=None)` — `GET /api/common/professions/`
### `common.interests(*, query=None)` — `GET /api/common/interests/`

---

## Exceptions

All raised from `rephonic`:

| Exception | Raised for |
|---|---|
| `RephonicError` | Base class for every error raised by the client |
| `APIConnectionError` | Network-level failure (DNS, timeout, TLS, connection refused) |
| `APIStatusError` | Base class for non-2xx responses |
| `BadRequestError` | HTTP 400 — includes "not found" cases (see note below) |
| `AuthenticationError` | HTTP 401 — missing or invalid API key |
| `PermissionDeniedError` | HTTP 403 |
| `NotFoundError` | HTTP 404 (reserved — the API does not currently use 404) |
| `RateLimitError` | HTTP 429 — quota or rate limit exceeded |
| `InternalServerError` | HTTP 5xx |

Every `APIStatusError` exposes `.status_code`, `.message`, `.body` (parsed JSON, if any), and `.response` (the underlying `httpx.Response`).

### "Not found" returns 400, not 404

The Rephonic API returns `400 Bad Request` for missing resources, not 404. To handle a missing podcast or episode, catch `BadRequestError` and check `.message` (examples: `"Podcast not found."`, `"Unknown episode."`, `"Unknown country."`):

```python
from rephonic import Rephonic, BadRequestError

client = Rephonic()
try:
    podcast = client.podcasts.get("does-not-exist")
except BadRequestError as exc:
    if "not found" in exc.message.lower() or "unknown" in exc.message.lower():
        print("Missing resource")
    else:
        raise
```
