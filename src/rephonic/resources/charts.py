"""Chart endpoints: category index and daily rankings."""

from __future__ import annotations

from typing import Any

from .._base_client import AsyncBaseClient, BaseClient, quote_path

ChartPlatform = str  # "apple" | "spotify" | "youtube"


class Charts:
    """Daily chart rankings from Apple Podcasts, Spotify, and YouTube."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def index(self, platform: ChartPlatform) -> dict[str, Any]:
        """Available countries and categories for a platform.

        ``platform`` is one of ``apple``, ``spotify``, ``youtube``. Use the
        returned ``slug`` values with :meth:`rankings`.
        """
        return self._client.get(f"/api/charts/{quote_path(platform)}/")

    def rankings(
        self,
        platform: ChartPlatform,
        *,
        country: str,
        category: str,
    ) -> dict[str, Any]:
        """Latest chart rankings for a platform + country + category.

        Updated every 24 hours. Use ``category="all"`` for the country's
        overall top chart.
        """
        return self._client.get(
            f"/api/charts/{quote_path(platform)}/{quote_path(country)}/{quote_path(category)}/"
        )


class AsyncCharts:
    """Async counterpart to :class:`Charts`."""

    def __init__(self, client: AsyncBaseClient) -> None:
        self._client = client

    async def index(self, platform: ChartPlatform) -> dict[str, Any]:
        return await self._client.get(f"/api/charts/{quote_path(platform)}/")

    async def rankings(
        self,
        platform: ChartPlatform,
        *,
        country: str,
        category: str,
    ) -> dict[str, Any]:
        return await self._client.get(
            f"/api/charts/{quote_path(platform)}/{quote_path(country)}/{quote_path(category)}/"
        )
