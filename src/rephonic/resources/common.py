"""Reference data endpoints: ``/api/common/*``.

These endpoints return reference data (categories, countries, languages,
sponsors, professions, interests) whose identifiers are used with the
``filters`` parameter on the search endpoints.
"""

from __future__ import annotations

from typing import Any

from .._base_client import AsyncBaseClient, BaseClient


class Common:
    """Reference data used with the ``filters`` parameter on search endpoints."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def categories(self) -> dict[str, Any]:
        """List every podcast category. IDs are used with the ``categories`` filter."""
        return self._client.get("/api/common/categories/")

    def countries(self) -> dict[str, Any]:
        """List every country. IDs are used with the ``locations`` filter."""
        return self._client.get("/api/common/countries/")

    def languages(self) -> dict[str, Any]:
        """List every language. Codes are used with the ``languages`` filter."""
        return self._client.get("/api/common/languages/")

    def sponsors(self, *, query: str | None = None) -> dict[str, Any]:
        """Commonly seen sponsors, optionally filtered by name."""
        return self._client.get("/api/common/sponsors/", params=dict(query=query))

    def professions(self, *, query: str | None = None) -> dict[str, Any]:
        """Common listener professions, optionally filtered by name."""
        return self._client.get("/api/common/professions/", params=dict(query=query))

    def interests(self, *, query: str | None = None) -> dict[str, Any]:
        """Common listener interests, optionally filtered by name."""
        return self._client.get("/api/common/interests/", params=dict(query=query))


class AsyncCommon:
    """Async counterpart to :class:`Common`."""

    def __init__(self, client: AsyncBaseClient) -> None:
        self._client = client

    async def categories(self) -> dict[str, Any]:
        return await self._client.get("/api/common/categories/")

    async def countries(self) -> dict[str, Any]:
        return await self._client.get("/api/common/countries/")

    async def languages(self) -> dict[str, Any]:
        return await self._client.get("/api/common/languages/")

    async def sponsors(self, *, query: str | None = None) -> dict[str, Any]:
        return await self._client.get("/api/common/sponsors/", params=dict(query=query))

    async def professions(self, *, query: str | None = None) -> dict[str, Any]:
        return await self._client.get("/api/common/professions/", params=dict(query=query))

    async def interests(self, *, query: str | None = None) -> dict[str, Any]:
        return await self._client.get("/api/common/interests/", params=dict(query=query))
