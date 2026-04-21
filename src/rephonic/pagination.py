"""Pagination helpers — sync and async.

The Rephonic API paginates via ``page`` / ``per_page`` query parameters. Each
paginated endpoint returns items under a fixed key (e.g. ``podcasts``,
``episodes``, ``reviews``) and the helpers here provide iterators that
transparently fetch subsequent pages.
"""

from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Iterator,
)


def _should_continue(response: dict[str, Any], num_items: int, per_page: int) -> bool:
    """Decide whether to request another page.

    ``more`` is authoritative when the endpoint returns it (search endpoints).
    Otherwise fall back to the "short page means last page" heuristic.
    """
    more = response.get("more")
    if more is True:
        return True
    if more is False:
        return False
    return num_items >= per_page


def iter_pages(
    fetch_page: Callable[[int, int], dict[str, Any]],
    *,
    items_key: str,
    per_page: int,
    start_page: int = 1,
    limit: int | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield items one at a time across paginated responses.

    Stops when the response's ``more`` field is ``False`` (or, for endpoints
    that don't send it, when the page is shorter than ``per_page``), or when
    ``limit`` is reached.
    """
    page = start_page
    yielded = 0
    while True:
        response = fetch_page(page, per_page)
        items = response.get(items_key) or []
        for item in items:
            if limit is not None and yielded >= limit:
                return
            yield item
            yielded += 1
        if not _should_continue(response, len(items), per_page):
            return
        page += 1


async def aiter_pages(
    fetch_page: Callable[[int, int], Awaitable[dict[str, Any]]],
    *,
    items_key: str,
    per_page: int,
    start_page: int = 1,
    limit: int | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Async counterpart to :func:`iter_pages`."""
    page = start_page
    yielded = 0
    while True:
        response = await fetch_page(page, per_page)
        items = response.get(items_key) or []
        for item in items:
            if limit is not None and yielded >= limit:
                return
            yield item
            yielded += 1
        if not _should_continue(response, len(items), per_page):
            return
        page += 1
