"""Official Python client for the Rephonic podcast API.

Quick start::

    from rephonic import Rephonic

    client = Rephonic(api_key="...")
    podcast = client.podcasts.get("huberman-lab")

Or async::

    from rephonic import AsyncRephonic

    async with AsyncRephonic(api_key="...") as client:
        podcast = await client.podcasts.get("huberman-lab")

See https://rephonic.com/developers for the full API reference.
"""

from ._client import AsyncRephonic, Rephonic
from ._exceptions import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    RephonicError,
)
from ._version import __version__
from .filters import FilterSpec

__all__ = [
    "Rephonic",
    "AsyncRephonic",
    "FilterSpec",
    "RephonicError",
    "APIConnectionError",
    "APIStatusError",
    "AuthenticationError",
    "BadRequestError",
    "PermissionDeniedError",
    "NotFoundError",
    "RateLimitError",
    "InternalServerError",
    "__version__",
]
