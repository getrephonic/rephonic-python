"""The top-level :class:`Rephonic` and :class:`AsyncRephonic` clients."""

from __future__ import annotations

import os
from typing import Any

import httpx

from ._base_client import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncBaseClient,
    BaseClient,
)
from .resources import (
    Account,
    AsyncAccount,
    AsyncCharts,
    AsyncCommon,
    AsyncEpisodes,
    AsyncPodcasts,
    AsyncSearch,
    Charts,
    Common,
    Episodes,
    Podcasts,
    Search,
)

ENV_API_KEY = "REPHONIC_API_KEY"


def _resolve_api_key(api_key: str | None) -> str:
    resolved = api_key or os.environ.get(ENV_API_KEY)
    if not resolved:
        raise ValueError(
            "No API key provided. Pass api_key=... or set the REPHONIC_API_KEY "
            "environment variable. Get one at https://rephonic.com/developers."
        )
    return resolved


class Rephonic:
    """Official Python client for the Rephonic podcast API.

    Get an API key at https://rephonic.com/developers.

    Args:
        api_key: Your Rephonic API key. Falls back to ``REPHONIC_API_KEY`` env.
        base_url: Override the API base URL.
        timeout: Request timeout in seconds.
        max_retries: Retries on connection errors, 429s, and 5xxs (default 2).
        http_client: Bring your own ``httpx.Client`` (for proxies, custom TLS).

    Example::

        from rephonic import Rephonic

        client = Rephonic(api_key="...")
        podcast = client.podcasts.get("huberman-lab")
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_client = BaseClient(
            api_key=_resolve_api_key(api_key),
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )

        self.search = Search(self._base_client)
        self.podcasts = Podcasts(self._base_client)
        self.episodes = Episodes(self._base_client)
        self.charts = Charts(self._base_client)
        self.common = Common(self._base_client)
        self.account = Account(self._base_client)

    def close(self) -> None:
        """Close the underlying HTTP client (if owned by this instance)."""
        self._base_client.close()

    def __enter__(self) -> Rephonic:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()


class AsyncRephonic:
    """Asynchronous client for the Rephonic podcast API.

    Same surface as :class:`Rephonic`, but every resource method is a
    coroutine. ``iter_*`` methods return async iterators.

    Example::

        from rephonic import AsyncRephonic

        async with AsyncRephonic(api_key="...") as client:
            podcast = await client.podcasts.get("huberman-lab")
            async for p in client.search.iter_podcasts(query="ai", limit=100):
                print(p["name"])
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_client = AsyncBaseClient(
            api_key=_resolve_api_key(api_key),
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )

        self.search = AsyncSearch(self._base_client)
        self.podcasts = AsyncPodcasts(self._base_client)
        self.episodes = AsyncEpisodes(self._base_client)
        self.charts = AsyncCharts(self._base_client)
        self.common = AsyncCommon(self._base_client)
        self.account = AsyncAccount(self._base_client)

    async def aclose(self) -> None:
        """Close the underlying async HTTP client (if owned by this instance)."""
        await self._base_client.aclose()

    async def __aenter__(self) -> AsyncRephonic:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()
