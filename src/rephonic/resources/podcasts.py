"""Podcast-scoped endpoints: metadata, people, rankings, demographics, contacts, reviews, etc."""

from __future__ import annotations

from typing import Any, Iterable

from .._base_client import AsyncBaseClient, BaseClient, quote_path

ReviewPlatform = str  # "all" | "apple" | "podchaser" | "castbox" | "audible" | "podaddict"
TrendMetric = str  # "downloads_per_episode" | "social_reach" | "spotify_followers"


def _csv(value: str | Iterable[str]) -> str:
    """Accept either a comma-separated string or an iterable of strings."""
    if isinstance(value, str):
        return value
    return ",".join(value)


class Podcasts:
    """Look up a podcast and all of its related data."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def lookup(
        self,
        *,
        itunes_id: int | str | None = None,
        feed_url: str | None = None,
        spotify_id: str | None = None,
        youtube_channel_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a podcast from an external identifier.

        Pass exactly one of ``itunes_id``, ``feed_url``, ``spotify_id``, or
        ``youtube_channel_id``. Returns ``{"podcasts": [...]}``, and the list
        is empty when nothing matches. More than one podcast can share a
        ``feed_url`` or ``youtube_channel_id``, and then the list has an entry
        for each. Pass the returned ``id`` to :meth:`get` and the other
        podcast methods.
        """
        return self._client.get(
            "/api/podcasts/lookup/",
            params=dict(
                itunes_id=itunes_id,
                feed_url=feed_url,
                spotify_id=spotify_id,
                youtube_channel_id=youtube_channel_id,
            ),
        )

    def get(self, podcast_id: str) -> dict[str, Any]:
        """Full metadata for one podcast, under ``{"podcast": {...}}``.

        Includes listener estimates, subscriber counts, ``entities`` (production
        company, network, agencies), ``links`` (website, media kit), ``badges``,
        guest and sponsor ``outreach`` (how to pitch, with ranked contacts),
        YouTube channel, similar podcasts, and the latest episode. Chart
        positions are in :meth:`rankings`.
        """
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/")

    def people(self, podcast_id: str) -> dict[str, Any]:
        """Hosts, crew, and recent guests with contacts and social accounts.

        Returns ``{"people": {"hosts": ..., "crew": ..., "guests": ...}}``.
        Hosts and crew carry a ``kind`` (``host``, ``producer``, ``booker``,
        etc.), a ``role`` label, and ``is_lead``: ``True`` for the current
        host(s) the show is fronted by, ``False`` for other hosts, ``None`` for
        crew and for shows not yet researched.
        """
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/people/")

    def rankings(self, podcast_id: str) -> dict[str, Any]:
        """Current Apple Podcasts, Spotify, and YouTube chart positions.

        Returns ``{"rankings": [...]}`` with one row per platform, country, and
        category the podcast ranks in. Empty when it doesn't currently chart.
        """
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/rankings/")

    def demographics(self, podcast_id: str) -> dict[str, Any]:
        """Estimated listener demographics: age, gender, education, income, interests, location."""
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/demographics/")

    def promotions(self, podcast_id: str) -> dict[str, Any]:
        """Sponsors and cross-promotions with ad text, promo codes, and URLs."""
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/promotions/")

    def contacts(self, podcast_id: str) -> dict[str, Any]:
        """Email contacts and contact pages ranked best first, plus social accounts.

        Returns ``{"contacts": [...], "social": [...]}``. Each contact has a
        ``medium`` of ``email`` or ``page``, a ``role``, and ``badges``.
        """
        return self._client.get("/api/contacts/", params=dict(podcast_id=podcast_id))

    def social(self, podcast_id: str) -> dict[str, Any]:
        """Social media accounts with follower and engagement metrics."""
        return self._client.get("/api/social/accounts/", params=dict(podcast_id=podcast_id))

    def feedback(self, podcast_id: str) -> dict[str, Any]:
        """Ratings and review counts for each app, plus AI-written review summaries.

        Each entry in ``feedback`` has the ``app`` (e.g. ``apple``,
        ``spotify``), its average ``rating``, and its ``ratings`` and
        ``reviews`` counts. ``insights`` is a list of AI-written sentences
        that summarise what listeners say in their reviews.
        """
        return self._client.get("/api/feedback/", params=dict(podcast_id=podcast_id))

    def reviews(self, podcast_id: str, *, platform: ReviewPlatform) -> dict[str, Any]:
        """Individual listener reviews, in chronological order.

        ``platform`` is one of ``all``, ``apple``, ``podchaser``, ``castbox``,
        ``audible``, ``podaddict``.
        """
        return self._client.get(
            "/api/reviews/", params=dict(podcast_id=podcast_id, platform=platform)
        )

    def trends(
        self,
        podcast_ids: str | Iterable[str],
        *,
        metrics: str | Iterable[str],
    ) -> dict[str, Any]:
        """Historical time series for one or more podcasts.

        ``podcast_ids`` accepts a string or iterable (max 3).
        ``metrics`` accepts a string or iterable (max 5). Allowed values:
        ``downloads_per_episode``, ``social_reach``, ``spotify_followers``.
        """
        return self._client.get(
            "/api/trends/",
            params=dict(podcast_ids=_csv(podcast_ids), metrics=_csv(metrics)),
        )

    def similar_graph(self, podcast_id: str) -> dict[str, Any]:
        """Graph of podcasts that share listeners with this one, as nodes and links."""
        return self._client.get("/api/similar/graph/", params=dict(podcast_id=podcast_id))


class AsyncPodcasts:
    """Async counterpart to :class:`Podcasts`."""

    def __init__(self, client: AsyncBaseClient) -> None:
        self._client = client

    async def lookup(
        self,
        *,
        itunes_id: int | str | None = None,
        feed_url: str | None = None,
        spotify_id: str | None = None,
        youtube_channel_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._client.get(
            "/api/podcasts/lookup/",
            params=dict(
                itunes_id=itunes_id,
                feed_url=feed_url,
                spotify_id=spotify_id,
                youtube_channel_id=youtube_channel_id,
            ),
        )

    async def get(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/")

    async def people(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/people/")

    async def rankings(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/rankings/")

    async def demographics(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/demographics/")

    async def promotions(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/promotions/")

    async def contacts(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get("/api/contacts/", params=dict(podcast_id=podcast_id))

    async def social(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get("/api/social/accounts/", params=dict(podcast_id=podcast_id))

    async def feedback(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get("/api/feedback/", params=dict(podcast_id=podcast_id))

    async def reviews(self, podcast_id: str, *, platform: ReviewPlatform) -> dict[str, Any]:
        return await self._client.get(
            "/api/reviews/", params=dict(podcast_id=podcast_id, platform=platform)
        )

    async def trends(
        self,
        podcast_ids: str | Iterable[str],
        *,
        metrics: str | Iterable[str],
    ) -> dict[str, Any]:
        return await self._client.get(
            "/api/trends/",
            params=dict(podcast_ids=_csv(podcast_ids), metrics=_csv(metrics)),
        )

    async def similar_graph(self, podcast_id: str) -> dict[str, Any]:
        return await self._client.get("/api/similar/graph/", params=dict(podcast_id=podcast_id))
