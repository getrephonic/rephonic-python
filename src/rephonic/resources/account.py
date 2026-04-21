"""Account endpoints: quota and usage."""

from __future__ import annotations

from typing import Any

from .._base_client import AsyncBaseClient, BaseClient


class Account:
    """Account-level endpoints."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client

    def quota(self) -> dict[str, Any]:
        """API request quota and usage for the current month."""
        return self._client.get("/api/accounts/quota/")


class AsyncAccount:
    """Async counterpart to :class:`Account`."""

    def __init__(self, client: AsyncBaseClient) -> None:
        self._client = client

    async def quota(self) -> dict[str, Any]:
        return await self._client.get("/api/accounts/quota/")
