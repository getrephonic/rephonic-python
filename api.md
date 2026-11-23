# API reference

This page lists every method on the Rephonic Python client and the HTTP endpoint it calls. The endpoints themselves are documented at [rephonic.com/developers](https://rephonic.com/developers).

All methods return `Dict[str, Any]` matching the raw JSON response from the API.

`AsyncRephonic` has an async version of every method below, with the same signature, and you `await` the call. On `AsyncRephonic` the `iter_*` methods return async iterators, which you loop over with `async for`.

---

## `Rephonic(api_key=None, *, base_url=..., api_version=None, timeout=30.0, max_retries=2, http_client=None)`

Synchronous client. Falls back to `REPHONIC_API_KEY` if `api_key` is omitted. Raises `ValueError` if neither is set. Supports use as a context manager (`with Rephonic() as client: ...`).

`api_version` is sent as the `X-Rephonic-Api-Version` header on every request. It falls back to `REPHONIC_API_VERSION`, then to the latest version (`1.1`). To choose a version, pass it, e.g. `api_version="1.1"`. An unknown version raises `BadRequestError` with the API's message.

## `AsyncRephonic(api_key=None, *, base_url=..., api_version=None, timeout=30.0, max_retries=2, http_client=None)`

Async client. Same constructor and resource attributes as `Rephonic`, but every method is a coroutine. Use with `async with AsyncRephonic() as client: ...`. Takes an `httpx.AsyncClient` for `http_client`.

---

## `client.search`

### `search.podcasts(*, query=None, mode=None, per_page=None, page=None, filters=None)`

`GET /api/search/podcasts/`

Searches podcasts by topic (the default), title or publisher. `filters` takes a dict that maps each field to a value or to an operator and its value, e.g. `{"listeners": {"gte": 5000}, "active": True, "categories": {"any": [1482, 1406]}}`. It also takes a list of raw clauses (`["listeners:gte:5000"]`) or a legacy comma-separated string. See the [Filters section in the README](./README.md#filters).

### `search.iter_podcasts(*, query=None, mode=None, filters=None, per_page=50, limit=None)`

Yields every matching podcast, fetching further pages as it goes. It stops after `limit` podcasts if you pass `limit`.

### `search.episodes(*, query=None, per_page=None, page=None, filters=None, highlight=None, podcast_id=None, threshold=None)`

`GET /api/search/episodes/`

Searches the text of episode titles, show notes and transcripts. `threshold=N` limits results to episodes published in the last N seconds (max 1,209,600). Poll with a small `threshold` to pick up new mentions of a brand.

### `search.iter_episodes(*, query=None, filters=None, highlight=None, podcast_id=None, threshold=None, per_page=50, limit=None)`

Yields every matching episode, fetching further pages as it goes.

### `search.autocomplete(*, mode, query)`

`GET /api/search/autocomplete/`

Suggests keywords and matching podcasts for a partial query. `mode` is one of `topics`, `titles`, `publishers`, `episodes`.

---

## `client.podcasts`

### `podcasts.lookup(*, itunes_id=None, feed_url=None, spotify_id=None, youtube_channel_id=None)`

`GET /api/podcasts/lookup/`

Finds a podcast from an external identifier. Pass exactly one of the four arguments. It returns `{"podcasts": [...]}`, and the list is empty when nothing matches. More than one podcast can share a `feed_url` or `youtube_channel_id`, and in that case the list has an entry for each of them. Pass the returned `id` to the other `podcasts.*` methods.

### `podcasts.get(podcast_id)`

`GET /api/podcasts/<id>/`

Returns the podcast's full metadata. This includes listener estimates (`downloads_per_episode`, `weekly_downloads`), subscriber counts, `entities` (production company, network, ad-sales or talent agency), `links` (`website` and `media-kit`), `badges`, the YouTube channel, similar podcasts and the latest episode. `guests` and `sponsors` each carry `accepted`, a `profile`, and an `outreach` block (`pitchable`, `instructions`, and ranked `contacts` in the same shape as `podcasts.contacts`). Chart positions are in `podcasts.rankings`.

### `podcasts.people(podcast_id)`

`GET /api/podcasts/<id>/people/`

Returns the hosts, crew and recent guests, with their contacts and social accounts. Each host and crew member has a `kind` (`host`, `producer`, `exec-producer`, `booker`, `editor`, `ad-sales` or `crew`) and a `role` label. They also have `is_lead`, which works like this:

- `true` for the current host or hosts who front the show. On an ensemble show with no single anchor, every current host is `true`.
- `false` for other hosts, e.g. former hosts or rotating hosts who appear beside an anchor.
- `null` for crew, and for shows Rephonic hasn't researched yet.

Each guest entry includes details of the episode they appeared on.

### `podcasts.rankings(podcast_id)`

`GET /api/podcasts/<id>/rankings/`

Returns the podcast's current positions in the Apple Podcasts, Spotify and YouTube charts as `{"rankings": [...]}`. There is one row per platform, country and category, each with its `rank`. The list is empty when the podcast isn't in any chart.

### `podcasts.demographics(podcast_id)`

`GET /api/podcasts/<id>/demographics/`

Returns estimated breakdowns of the podcast's listeners by age, gender, education, profession, income, interests, parenting, relationship status and country.

### `podcasts.promotions(podcast_id)`

`GET /api/podcasts/<id>/promotions/`

Returns the sponsors and cross-promotions that have run on the podcast, with their ad text, promo codes and URLs.

### `podcasts.contacts(podcast_id)`

`GET /api/contacts/`

Returns the podcast's email contacts and contact pages in one list, ranked best first, plus its social accounts. Each contact has a `medium`, `badges` and quality fields such as `verification_status`, `warning`, `upvotes` and `downvotes`.

### `podcasts.social(podcast_id)`

`GET /api/social/accounts/`

Returns the podcast's social media accounts with follower and engagement numbers. The channels are `instagram`, `facebook`, `twitter`, `patreon`, `tiktok`, `soundcloud`, `pinterest`, `linkedin_profile`, `linkedin_group` and `clubhouse_club`.

### `podcasts.feedback(podcast_id)`

`GET /api/feedback/`

Returns one entry per app (e.g. `apple`, `spotify`, `podchaser`) with its average `rating` and its counts of `ratings` and `reviews`. It also returns `insights`, a list of AI-written sentences that summarise what listeners say in their reviews.

### `podcasts.reviews(podcast_id, *, platform)`

`GET /api/reviews/`

Returns individual listener reviews. `platform` is one of `all`, `apple`, `podchaser`, `castbox`, `audible`, `podaddict`.

### `podcasts.trends(podcast_ids, *, metrics)`

`GET /api/trends/`

Returns the history of each metric over time. `podcast_ids` takes a single ID or an iterable of up to 3. `metrics` takes a single metric or an iterable of up to 5. The allowed metrics are `downloads_per_episode`, `social_reach` and `spotify_followers`.

### `podcasts.similar_graph(podcast_id)`

`GET /api/similar/graph/`

Returns a graph of podcasts whose listeners overlap with this one, as `nodes` and `links`.

---

## `client.episodes`

### `episodes.list(*, podcast_id, query=None, per_page=None, page=None)`

`GET /api/episodes/`

Returns a podcast's episodes in chronological order.

### `episodes.iter_list(*, podcast_id, query=None, per_page=25, limit=None)`

Yields every episode of the podcast, fetching further pages as it goes.

### `episodes.get(episode_id)`

`GET /api/episodes/<id>/`

Returns the episode's full metadata, including topics, guests, hosts, sponsors, key moments, Q&A extracts, tone, locations and safety tags.

### `episodes.transcript(episode_id)`

`GET /api/episodes/<id>/transcript/`

Returns the transcript as timestamped segments, each with a speaker ID. When Rephonic has identified the speakers, it also returns a map from speaker ID to name.

---

## `client.charts`

### `charts.index(platform)`

`GET /api/charts/<platform>/`

Returns the countries and categories that have charts on `platform`, which is one of `apple`, `spotify` or `youtube`.

### `charts.rankings(platform, *, country, category)`

`GET /api/charts/<platform>/<country>/<category>/`

Returns the latest rankings for one chart. Rephonic updates them every 24 hours. Use `category="all"` for the overall top chart. For one podcast's positions across every chart, use `podcasts.rankings`.

---

## `client.common`

These methods return the values you can use in the `filters` parameter on search endpoints.

| Method | Endpoint |
|---|---|
| `common.categories()` | `GET /api/common/categories/` |
| `common.countries()` | `GET /api/common/countries/` |
| `common.languages()` | `GET /api/common/languages/` |
| `common.sponsors(*, query=None)` | `GET /api/common/sponsors/` |
| `common.professions(*, query=None)` | `GET /api/common/professions/` |
| `common.interests(*, query=None)` | `GET /api/common/interests/` |

---

## Exceptions

All raised from `rephonic`:

| Exception | Raised for |
|---|---|
| `RephonicError` | Base class for every error raised by the client |
| `APIConnectionError` | Network-level failure (DNS, timeout, TLS, connection refused) |
| `APIStatusError` | Base class for non-2xx responses |
| `BadRequestError` | HTTP 400, which the API also uses for "not found" (see the note below) and for unknown or retired API versions |
| `AuthenticationError` | HTTP 401, for a missing or invalid API key |
| `PermissionDeniedError` | HTTP 403 |
| `NotFoundError` | HTTP 404 (reserved, because the API doesn't use 404 at the moment) |
| `RateLimitError` | HTTP 429, when you've used up your quota or hit the rate limit |
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
