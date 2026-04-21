"""Search endpoints: ``/api/search/*``."""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from .._base_client import AsyncBaseClient, BaseClient
from ..filters import FilterSpec, encode_filters
from ..pagination import aiter_pages, iter_pages

SearchMode = str  # "topics" | "titles" | "publishers"
AutocompleteMode = str  # "topics" | "titles" | "publishers" | "episodes"


def _podcast_params(
    query: str | None,
    mode: str | None,
    per_page: int | None,
    page: int | None,
    filters: FilterSpec,
) -> dict[str, Any]:
    return dict(
        query=query,
        mode=mode,
        per_page=per_page,
        page=page,
        filters=encode_filters(filters),
    )


def _episode_params(
    query: str | None,
    per_page: int | None,
    page: int | None,
    filters: FilterSpec,
    highlight: bool | None,
    podcast_id: str | None,
    threshold: int | None,
) -> dict[str, Any]:
    return dict(
        query=query,
        per_page=per_page,
        page=page,
        filters=encode_filters(filters),
        highlight=highlight,
        podcast_id=podcast_id,
        threshold=threshold,
    )


class Search:
    """Search for podcasts and episodes, and get autocomplete suggestions."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def podcasts(
        self,
        *,
        query: str | None = None,
        mode: SearchMode | None = None,
        per_page: int | None = None,
        page: int | None = None,
        filters: FilterSpec = None,
    ) -> dict[str, Any]:
        """Search for podcasts by topic, title, or publisher.

        Specify either ``query``, ``filters``, or both.
        """
        return self._client.get(
            "/api/search/podcasts/",
            params=_podcast_params(query, mode, per_page, page, filters),
        )

    def iter_podcasts(
        self,
        *,
        query: str | None = None,
        mode: SearchMode | None = None,
        filters: FilterSpec = None,
        per_page: int = 50,
        limit: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterate over all matching podcasts, auto-fetching subsequent pages."""

        def fetch(page: int, per_page: int) -> dict[str, Any]:
            return self.podcasts(
                query=query, mode=mode, filters=filters, per_page=per_page, page=page
            )

        return iter_pages(fetch, items_key="podcasts", per_page=per_page, limit=limit)

    def episodes(
        self,
        *,
        query: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
        filters: FilterSpec = None,
        highlight: bool | None = None,
        podcast_id: str | None = None,
        threshold: int | None = None,
    ) -> dict[str, Any]:
        """Full-text search across episode titles, show notes, and transcripts.

        ``threshold`` restricts results to episodes published in the last N
        seconds (max 1,209,600 = 14 days). Useful for near-realtime monitoring.
        """
        return self._client.get(
            "/api/search/episodes/",
            params=_episode_params(
                query, per_page, page, filters, highlight, podcast_id, threshold
            ),
        )

    def iter_episodes(
        self,
        *,
        query: str | None = None,
        filters: FilterSpec = None,
        highlight: bool | None = None,
        podcast_id: str | None = None,
        threshold: int | None = None,
        per_page: int = 50,
        limit: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterate over all matching episodes, auto-fetching subsequent pages."""

        def fetch(page: int, per_page: int) -> dict[str, Any]:
            return self.episodes(
                query=query,
                filters=filters,
                highlight=highlight,
                podcast_id=podcast_id,
                threshold=threshold,
                per_page=per_page,
                page=page,
            )

        return iter_pages(fetch, items_key="episodes", per_page=per_page, limit=limit)

    def autocomplete(self, *, mode: AutocompleteMode, query: str) -> dict[str, Any]:
        """Get suggested keywords and matching podcasts for a partial query."""
        return self._client.get("/api/search/autocomplete/", params=dict(mode=mode, query=query))


class AsyncSearch:
    """Async counterpart to :class:`Search`."""

    def __init__(self, client: AsyncBaseClient) -> None:
        self._client = client

    async def podcasts(
        self,
        *,
        query: str | None = None,
        mode: SearchMode | None = None,
        per_page: int | None = None,
        page: int | None = None,
        filters: FilterSpec = None,
    ) -> dict[str, Any]:
        return await self._client.get(
            "/api/search/podcasts/",
            params=_podcast_params(query, mode, per_page, page, filters),
        )

    def iter_podcasts(
        self,
        *,
        query: str | None = None,
        mode: SearchMode | None = None,
        filters: FilterSpec = None,
        per_page: int = 50,
        limit: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        async def fetch(page: int, per_page: int) -> dict[str, Any]:
            return await self.podcasts(
                query=query, mode=mode, filters=filters, per_page=per_page, page=page
            )

        return aiter_pages(fetch, items_key="podcasts", per_page=per_page, limit=limit)

    async def episodes(
        self,
        *,
        query: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
        filters: FilterSpec = None,
        highlight: bool | None = None,
        podcast_id: str | None = None,
        threshold: int | None = None,
    ) -> dict[str, Any]:
        return await self._client.get(
            "/api/search/episodes/",
            params=_episode_params(
                query, per_page, page, filters, highlight, podcast_id, threshold
            ),
        )

    def iter_episodes(
        self,
        *,
        query: str | None = None,
        filters: FilterSpec = None,
        highlight: bool | None = None,
        podcast_id: str | None = None,
        threshold: int | None = None,
        per_page: int = 50,
        limit: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        async def fetch(page: int, per_page: int) -> dict[str, Any]:
            return await self.episodes(
                query=query,
                filters=filters,
                highlight=highlight,
                podcast_id=podcast_id,
                threshold=threshold,
                per_page=per_page,
                page=page,
            )

        return aiter_pages(fetch, items_key="episodes", per_page=per_page, limit=limit)

    async def autocomplete(self, *, mode: AutocompleteMode, query: str) -> dict[str, Any]:
        return await self._client.get(
            "/api/search/autocomplete/", params=dict(mode=mode, query=query)
        )
