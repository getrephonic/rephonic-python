import httpx
import pytest
import respx

from rephonic import (
    APIConnectionError,
    AsyncRephonic,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)


async def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("REPHONIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="No API key provided"):
        AsyncRephonic()


async def test_env_var_fallback(monkeypatch):
    monkeypatch.setenv("REPHONIC_API_KEY", "from-env")
    async with AsyncRephonic() as client:
        assert client._base_client._api_key == "from-env"


@respx.mock
async def test_sends_auth_header(aclient):
    route = respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(200, json=dict(usage=1, quota=10000))
    )
    await aclient.account.quota()
    assert route.called
    assert route.calls.last.request.headers["x-rephonic-api-key"] == "test-key"


@respx.mock
async def test_podcast_get(aclient):
    respx.get("https://api.rephonic.com/api/podcasts/huberman-lab/").mock(
        return_value=httpx.Response(200, json=dict(podcast=dict(id="huberman-lab")))
    )
    result = await aclient.podcasts.get("huberman-lab")
    assert result["podcast"]["id"] == "huberman-lab"


@respx.mock
async def test_podcast_lookup(aclient):
    route = respx.get("https://api.rephonic.com/api/podcasts/lookup/").mock(
        return_value=httpx.Response(200, json=dict(podcasts=[dict(id="huberman-lab")]))
    )
    result = await aclient.podcasts.lookup(spotify_id="79CkJF3UJTHFV8Dse3Oy0P")
    assert result["podcasts"][0]["id"] == "huberman-lab"
    params = route.calls.last.request.url.params
    assert params["spotify_id"] == "79CkJF3UJTHFV8Dse3Oy0P"


@respx.mock
async def test_search_podcasts(aclient):
    route = respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        return_value=httpx.Response(200, json=dict(podcasts=[dict(id="x")], more=False))
    )
    result = await aclient.search.podcasts(query="ai", per_page=10)
    assert result["podcasts"][0]["id"] == "x"
    assert route.calls.last.request.url.params["query"] == "ai"


@respx.mock
@pytest.mark.parametrize(
    "status,expected",
    [
        (401, AuthenticationError),
        (404, NotFoundError),
        (429, RateLimitError),
    ],
)
async def test_error_mapping(aclient, status, expected):
    respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(status, json=dict(error="nope"))
    )
    with pytest.raises(expected) as exc:
        await aclient.account.quota()
    assert exc.value.status_code == status


@respx.mock
async def test_connection_error_wrapped(aclient):
    respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        side_effect=httpx.ConnectError("boom")
    )
    with pytest.raises(APIConnectionError):
        await aclient.account.quota()


@respx.mock
async def test_iter_podcasts_paginates(aclient):
    respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        side_effect=[
            httpx.Response(
                200,
                json=dict(podcasts=[dict(id="a"), dict(id="b")], page=1, per_page=2, more=True),
            ),
            httpx.Response(
                200,
                json=dict(podcasts=[dict(id="c")], page=2, per_page=2, more=False),
            ),
        ]
    )
    ids = []
    async for p in aclient.search.iter_podcasts(per_page=2):
        ids.append(p["id"])
    assert ids == ["a", "b", "c"]


@respx.mock
async def test_iter_podcasts_respects_limit(aclient):
    respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        return_value=httpx.Response(
            200,
            json=dict(
                podcasts=[dict(id=str(i)) for i in range(50)],
                page=1,
                per_page=50,
                more=True,
            ),
        )
    )
    ids = []
    async for p in aclient.search.iter_podcasts(per_page=50, limit=3):
        ids.append(p["id"])
    assert ids == ["0", "1", "2"]


@respx.mock
async def test_context_manager_closes():
    async with AsyncRephonic(api_key="test-key", max_retries=0) as client:
        respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
            return_value=httpx.Response(200, json=dict(usage=1, quota=1))
        )
        await client.account.quota()
    assert client._base_client._http_client.is_closed
