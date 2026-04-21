"""Low-level HTTP transport shared by all resources.

Two flavours live here: :class:`BaseClient` (sync, uses ``httpx.Client``) and
:class:`AsyncBaseClient` (async, uses ``httpx.AsyncClient``). Resource classes
hold a reference to one of these and dispatch HTTP requests through it.
"""

from __future__ import annotations

import asyncio
import json
import random
import time
from typing import Any, Mapping, Union
from urllib.parse import quote

import httpx

from ._exceptions import APIConnectionError, error_for_status
from ._version import __version__


def quote_path(segment: str) -> str:
    """URL-encode a path segment so callers can't break out of the path.

    ``safe=""`` means slashes, dots, and other reserved characters are all
    percent-encoded. Use for every user-supplied value interpolated into a
    path (podcast_id, episode_id, platform, country, category).
    """
    return quote(str(segment), safe="")

DEFAULT_BASE_URL = "https://api.rephonic.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2

QueryValue = Union[str, int, float, bool, None]
Query = Mapping[str, QueryValue]


def _validate_api_key(api_key: str) -> None:
    if not api_key:
        raise ValueError(
            "No API key provided. Pass api_key=... or set the REPHONIC_API_KEY "
            "environment variable. Get one at https://rephonic.com/developers."
        )


def _validate_max_retries(max_retries: int) -> None:
    if max_retries < 0:
        raise ValueError(f"max_retries must be >= 0, got {max_retries}")


def _default_headers() -> dict[str, str]:
    return {"User-Agent": f"rephonic-python/{__version__}"}


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"X-Rephonic-Api-Key": api_key}


class BaseClient:
    """Synchronous HTTP transport: auth, retries, error mapping.

    Resource classes receive a ``BaseClient`` and call :meth:`request` with a
    relative path and optional query params.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
    ) -> None:
        _validate_api_key(api_key)
        _validate_max_retries(max_retries)
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._owns_http_client = http_client is None
        self._http_client = http_client or httpx.Client(timeout=timeout, headers=_default_headers())

    def close(self) -> None:
        """Close the underlying HTTP client if it was created by this instance."""
        if self._owns_http_client:
            self._http_client.close()

    def __enter__(self) -> BaseClient:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Query | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request and return the parsed JSON body.

        Retries on connection errors and on 429/5xx responses, with exponential
        backoff plus jitter (or ``Retry-After`` when the server sends it).
        """
        url = f"{self._base_url}{path}"
        cleaned = _clean_params(params) if params else None
        headers = _auth_headers(self._api_key)

        last_error: BaseException | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._http_client.request(method, url, params=cleaned, headers=headers)
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise APIConnectionError(f"Unable to reach Rephonic API: {exc}") from exc
                time.sleep(_backoff_delay(attempt))
                continue

            if response.status_code < 400:
                return _parse_json(response)

            if _should_retry_status(response.status_code) and attempt < self._max_retries:
                time.sleep(_sleep_for_response(attempt, response))
                continue

            raise _build_status_error(response)

        assert last_error is not None
        raise APIConnectionError(str(last_error)) from last_error

    def get(self, path: str, *, params: Query | None = None) -> dict[str, Any]:
        return self.request("GET", path, params=params)


class AsyncBaseClient:
    """Asynchronous HTTP transport. Mirrors :class:`BaseClient`."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        _validate_api_key(api_key)
        _validate_max_retries(max_retries)
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._owns_http_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient(
            timeout=timeout, headers=_default_headers()
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client if it was created by this instance."""
        if self._owns_http_client:
            await self._http_client.aclose()

    async def __aenter__(self) -> AsyncBaseClient:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Query | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        cleaned = _clean_params(params) if params else None
        headers = _auth_headers(self._api_key)

        last_error: BaseException | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._http_client.request(
                    method, url, params=cleaned, headers=headers
                )
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise APIConnectionError(f"Unable to reach Rephonic API: {exc}") from exc
                await asyncio.sleep(_backoff_delay(attempt))
                continue

            if response.status_code < 400:
                return _parse_json(response)

            if _should_retry_status(response.status_code) and attempt < self._max_retries:
                await asyncio.sleep(_sleep_for_response(attempt, response))
                continue

            raise _build_status_error(response)

        assert last_error is not None
        raise APIConnectionError(str(last_error)) from last_error

    async def get(self, path: str, *, params: Query | None = None) -> dict[str, Any]:
        return await self.request("GET", path, params=params)


def _clean_params(params: Query) -> dict[str, str]:
    """Drop ``None`` values and coerce booleans to lowercase strings."""
    out: dict[str, str] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = "true" if value else "false"
        else:
            out[key] = str(value)
    return out


def _parse_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        raise APIConnectionError(
            f"Rephonic API returned non-JSON response (status {response.status_code})"
        ) from exc
    if not isinstance(data, dict):
        raise APIConnectionError(
            f"Rephonic API returned unexpected JSON shape: {type(data).__name__}"
        )
    return data


def _build_status_error(response: httpx.Response) -> Exception:
    body: dict[str, Any] | None = None
    try:
        parsed = response.json()
        if isinstance(parsed, dict):
            body = parsed
    except json.JSONDecodeError:
        pass
    message = (body or {}).get("error") or response.text or response.reason_phrase
    return error_for_status(response.status_code, message, body=body, response=response)


def _should_retry_status(status: int) -> bool:
    return status == 429 or status >= 500


def _backoff_delay(attempt: int) -> float:
    return float(min(2**attempt, 10)) + random.uniform(0, 0.25)


def _sleep_for_response(attempt: int, response: httpx.Response) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return float(retry_after)
        except ValueError:
            pass
    return _backoff_delay(attempt)
