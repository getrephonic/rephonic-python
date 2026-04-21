"""Episode endpoints: list, get, transcript."""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from .._base_client import AsyncBaseClient, BaseClient, quote_path
from ..pagination import aiter_pages, iter_pages


def _list_params(
    podcast_id: str,
    query: str | None,
    per_page: int | None,
    page: int | None,
) -> dict[str, Any]:
    return dict(podcast_id=podcast_id, query=query, per_page=per_page, page=page)


class Episodes:
    """List and look up episodes, and get full transcripts."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def list(
        self,
        *,
        podcast_id: str,
        query: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> dict[str, Any]:
        """Every episode for a podcast in chronological order.

        ``per_page`` maxes out at 25. If ``audio_url`` is ``null``, the audio is
        hosted by Apple Podcasts and ``itunes_id`` will be set instead.
        """
        return self._client.get(
            "/api/episodes/",
            params=_list_params(podcast_id, query, per_page, page),
        )

    def iter_list(
        self,
        *,
        podcast_id: str,
        query: str | None = None,
        per_page: int = 25,
        limit: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterate over every episode for a podcast, auto-fetching pages."""

        def fetch(page: int, per_page: int) -> dict[str, Any]:
            return self.list(podcast_id=podcast_id, query=query, per_page=per_page, page=page)

        return iter_pages(fetch, items_key="episodes", per_page=per_page, limit=limit)

    def get(self, episode_id: str) -> dict[str, Any]:
        """Full episode metadata including topics, guests, hosts, sponsors, key moments, Q&A."""
        return self._client.get(f"/api/episodes/{quote_path(episode_id)}/")

    def transcript(self, episode_id: str) -> dict[str, Any]:
        """Timestamped transcript segments with speaker IDs and a name mapping where detected.

        Not available for every episode.
        """
        return self._client.get(f"/api/episodes/{quote_path(episode_id)}/transcript/")


class AsyncEpisodes:
    """Async counterpart to :class:`Episodes`."""

    def __init__(self, client: AsyncBaseClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        podcast_id: str,
        query: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> dict[str, Any]:
        return await self._client.get(
            "/api/episodes/",
            params=_list_params(podcast_id, query, per_page, page),
        )

    def iter_list(
        self,
        *,
        podcast_id: str,
        query: str | None = None,
        per_page: int = 25,
        limit: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        async def fetch(page: int, per_page: int) -> dict[str, Any]:
            return await self.list(podcast_id=podcast_id, query=query, per_page=per_page, page=page)

        return aiter_pages(fetch, items_key="episodes", per_page=per_page, limit=limit)

    async def get(self, episode_id: str) -> dict[str, Any]:
        return await self._client.get(f"/api/episodes/{quote_path(episode_id)}/")

    async def transcript(self, episode_id: str) -> dict[str, Any]:
        return await self._client.get(f"/api/episodes/{quote_path(episode_id)}/transcript/")
