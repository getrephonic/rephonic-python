"""Podcast-scoped endpoints: metadata, people, demographics, contacts, reviews, etc."""

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
        ``youtube_channel_id``. Returns ``{"podcasts": [...]}`` — the list
        is empty when no match is found, and may contain multiple entries
        for ``feed_url`` / ``youtube_channel_id`` when the identifier is
        shared. Use the returned ``id`` with :meth:`get` and the other
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
        """Full metadata, chart rankings, YouTube channel, similar podcasts, and latest episode."""
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/")

    def people(self, podcast_id: str) -> dict[str, Any]:
        """Hosts and recent guests with contacts and social accounts."""
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/people/")

    def demographics(self, podcast_id: str) -> dict[str, Any]:
        """Estimated listener demographics: age, gender, education, income, interests, location."""
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/demographics/")

    def promotions(self, podcast_id: str) -> dict[str, Any]:
        """Sponsors and cross-promotions with ad text, promo codes, and URLs."""
        return self._client.get(f"/api/podcasts/{quote_path(podcast_id)}/promotions/")

    def contacts(self, podcast_id: str) -> dict[str, Any]:
        """Email contacts, contact pages, and social accounts with quality signals."""
        return self._client.get("/api/contacts/", params=dict(podcast_id=podcast_id))

    def social(self, podcast_id: str) -> dict[str, Any]:
        """Social media accounts with follower and engagement metrics."""
        return self._client.get("/api/social/accounts/", params=dict(podcast_id=podcast_id))

    def feedback(self, podcast_id: str) -> dict[str, Any]:
        """Overall ratings across apps plus AI-generated summary insights."""
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
        """Shared-audience graph (nodes + links) of podcasts with overlapping listeners."""
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
