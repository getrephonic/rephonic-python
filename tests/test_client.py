import httpx
import pytest
import respx

from rephonic import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    RateLimitError,
    Rephonic,
    RephonicError,
)


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("REPHONIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="No API key provided"):
        Rephonic()


def test_rejects_negative_max_retries():
    with pytest.raises(ValueError, match="max_retries must be >= 0"):
        Rephonic(api_key="test", max_retries=-1)


def test_falls_back_to_env_var(monkeypatch):
    monkeypatch.setenv("REPHONIC_API_KEY", "from-env")
    with Rephonic() as client:
        assert client._base_client._api_key == "from-env"


@respx.mock
def test_sends_auth_header(client):
    route = respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(200, json=dict(usage=1, quota=10000))
    )
    client.account.quota()
    assert route.called
    assert route.calls.last.request.headers["x-rephonic-api-key"] == "test-key"


@respx.mock
def test_sends_user_agent(client):
    route = respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(200, json=dict(usage=1, quota=1))
    )
    client.account.quota()
    ua = route.calls.last.request.headers["user-agent"]
    assert ua.startswith("rephonic-python/")


@respx.mock
@pytest.mark.parametrize(
    "status,expected",
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (404, NotFoundError),
        (429, RateLimitError),
        (500, InternalServerError),
        (503, InternalServerError),
    ],
)
def test_maps_status_codes_to_errors(client, status, expected):
    respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(status, json=dict(error="nope"))
    )
    with pytest.raises(expected) as exc:
        client.account.quota()
    assert exc.value.status_code == status
    assert exc.value.message == "nope"
    assert isinstance(exc.value, RephonicError)


@respx.mock
def test_connection_error_wrapped(client):
    respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(APIConnectionError):
        client.account.quota()


@respx.mock
def test_context_manager_closes_client():
    with Rephonic(api_key="test-key", max_retries=0) as client:
        respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
            return_value=httpx.Response(200, json=dict(usage=1, quota=1))
        )
        client.account.quota()
    assert client._base_client._http_client.is_closed


@respx.mock
def test_booleans_serialized_lowercase(client):
    route = respx.get("https://api.rephonic.com/api/search/episodes/").mock(
        return_value=httpx.Response(200, json=dict(episodes=[], more=False))
    )
    client.search.episodes(query="x", highlight=True)
    assert route.calls.last.request.url.params["highlight"] == "true"


@respx.mock
def test_none_params_omitted(client):
    route = respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        return_value=httpx.Response(200, json=dict(podcasts=[], more=False))
    )
    client.search.podcasts(query="ai")
    params = route.calls.last.request.url.params
    assert "query" in params
    assert "mode" not in params
    assert "filters" not in params
