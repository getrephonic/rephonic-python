"""Exception classes raised by the Rephonic client."""

from typing import Any, Dict, Optional


class RephonicError(Exception):
    """Base class for all Rephonic client errors.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code, or ``None`` for non-HTTP errors.
        body: Parsed JSON body of the error response, if available.
        response: The underlying ``httpx.Response`` object, if available.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        body: Optional[Dict[str, Any]] = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.body = body
        self.response = response

    def __str__(self) -> str:
        if self.status_code is not None:
            return f"[{self.status_code}] {self.message}"
        return self.message


class APIConnectionError(RephonicError):
    """Raised when the client cannot reach the Rephonic API (network error, DNS, timeout)."""


class APIStatusError(RephonicError):
    """Base class for errors returned by the API with a non-2xx status code."""


class BadRequestError(APIStatusError):
    """Raised for HTTP 400 responses. Usually indicates a malformed request or invalid parameter."""


class AuthenticationError(APIStatusError):
    """Raised for HTTP 401 responses. Indicates a missing or invalid API key."""


class PermissionDeniedError(APIStatusError):
    """Raised for HTTP 403 responses. The API key is valid but lacks access to the resource."""


class NotFoundError(APIStatusError):
    """Raised for HTTP 404 responses.

    Note: the Rephonic API returns ``400 Bad Request`` (``BadRequestError``)
    for missing resources, not 404 — this class is reserved for future use
    and for explicitly catching any endpoint that might adopt 404 semantics.
    """


class RateLimitError(APIStatusError):
    """Raised for HTTP 429 responses. You have exceeded your request quota or rate limit."""


class InternalServerError(APIStatusError):
    """Raised for HTTP 5xx responses. The Rephonic API is experiencing an internal error."""


_STATUS_TO_ERROR = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    429: RateLimitError,
}


def error_for_status(
    status_code: int,
    message: str,
    *,
    body: Optional[Dict[str, Any]] = None,
    response: Any = None,
) -> APIStatusError:
    """Map an HTTP status code to the most specific error subclass."""
    cls = _STATUS_TO_ERROR.get(status_code)
    if cls is None:
        cls = InternalServerError if status_code >= 500 else APIStatusError
    return cls(message, status_code=status_code, body=body, response=response)
