import httpx
import respx


@respx.mock
def test_search_podcasts(client):
    route = respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        return_value=httpx.Response(200, json=dict(podcasts=[dict(id="x")], more=False))
    )
    result = client.search.podcasts(
        query="ai", mode="topics", per_page=10, filters="listeners:gte:5000"
    )
    assert result["podcasts"][0]["id"] == "x"
    params = route.calls.last.request.url.params
    assert params["query"] == "ai"
    assert params["mode"] == "topics"
    assert params["per_page"] == "10"
    assert params["filters"] == "listeners:gte:5000"


@respx.mock
def test_autocomplete(client):
    respx.get("https://api.rephonic.com/api/search/autocomplete/").mock(
        return_value=httpx.Response(200, json=dict(suggestions=["a"], podcasts=[]))
    )
    result = client.search.autocomplete(mode="topics", query="mark")
    assert result["suggestions"] == ["a"]


@respx.mock
def test_podcast_get_encodes_path(client):
    route = respx.get("https://api.rephonic.com/api/podcasts/huberman-lab/").mock(
        return_value=httpx.Response(200, json=dict(podcast=dict(id="huberman-lab")))
    )
    result = client.podcasts.get("huberman-lab")
    assert result["podcast"]["id"] == "huberman-lab"
    assert route.called


@respx.mock
def test_path_param_cannot_traverse(client):
    """A malicious podcast_id containing slashes must not break out of the path."""
    route = respx.get(
        "https://api.rephonic.com/api/podcasts/..%2Fadmin/people/"
    ).mock(return_value=httpx.Response(200, json=dict(people=dict(hosts=dict(list=[])))))
    client.podcasts.people("../admin")
    assert route.called, "Expected the slashes in podcast_id to be percent-encoded"


@respx.mock
def test_path_param_encodes_spaces(client):
    route = respx.get("https://api.rephonic.com/api/podcasts/foo%20bar/").mock(
        return_value=httpx.Response(200, json=dict(podcast=dict(id="foo bar")))
    )
    client.podcasts.get("foo bar")
    assert route.called


@respx.mock
def test_podcast_contacts_passes_query(client):
    route = respx.get("https://api.rephonic.com/api/contacts/").mock(
        return_value=httpx.Response(200, json=dict(contacts=dict(email=[])))
    )
    client.podcasts.contacts("the-daily")
    assert route.calls.last.request.url.params["podcast_id"] == "the-daily"


@respx.mock
def test_reviews_requires_platform(client):
    route = respx.get("https://api.rephonic.com/api/reviews/").mock(
        return_value=httpx.Response(200, json=dict(reviews=[], page=1, per_page=20, count=0))
    )
    client.podcasts.reviews("huberman-lab", platform="apple")
    params = route.calls.last.request.url.params
    assert params["podcast_id"] == "huberman-lab"
    assert params["platform"] == "apple"


@respx.mock
def test_trends_accepts_list_or_string(client):
    route = respx.get("https://api.rephonic.com/api/trends/").mock(
        return_value=httpx.Response(200, json=dict(trends=dict()))
    )
    client.podcasts.trends(
        ["huberman-lab", "the-daily"], metrics=["downloads_per_episode", "social_reach"]
    )
    params = route.calls.last.request.url.params
    assert params["podcast_ids"] == "huberman-lab,the-daily"
    assert params["metrics"] == "downloads_per_episode,social_reach"

    client.podcasts.trends("huberman-lab", metrics="social_reach")
    params = route.calls.last.request.url.params
    assert params["podcast_ids"] == "huberman-lab"
    assert params["metrics"] == "social_reach"


@respx.mock
def test_episodes_list(client):
    route = respx.get("https://api.rephonic.com/api/episodes/").mock(
        return_value=httpx.Response(
            200, json=dict(episodes=[dict(id="e1")], page=1, per_page=25, total_count=1)
        )
    )
    client.episodes.list(podcast_id="the-daily", query="x", per_page=10)
    params = route.calls.last.request.url.params
    assert params["podcast_id"] == "the-daily"
    assert params["query"] == "x"
    assert params["per_page"] == "10"
    assert route.called


@respx.mock
def test_episode_transcript(client):
    respx.get("https://api.rephonic.com/api/episodes/abc123/transcript/").mock(
        return_value=httpx.Response(
            200, json=dict(transcript=dict(segments=[]), episode=dict(id="abc123"))
        )
    )
    result = client.episodes.transcript("abc123")
    assert "transcript" in result


@respx.mock
def test_charts_index(client):
    respx.get("https://api.rephonic.com/api/charts/apple/").mock(
        return_value=httpx.Response(200, json=dict(categories=[], countries=[]))
    )
    result = client.charts.index("apple")
    assert "categories" in result


@respx.mock
def test_charts_rankings(client):
    route = respx.get("https://api.rephonic.com/api/charts/apple/united-states/technology/").mock(
        return_value=httpx.Response(200, json=dict(podcasts=[]))
    )
    client.charts.rankings("apple", country="united-states", category="technology")
    assert route.called


@respx.mock
def test_common_sponsors_with_query(client):
    route = respx.get("https://api.rephonic.com/api/common/sponsors/").mock(
        return_value=httpx.Response(200, json=dict(sponsors=[]))
    )
    client.common.sponsors(query="acme")
    assert route.calls.last.request.url.params["query"] == "acme"


@respx.mock
def test_account_quota(client):
    respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(200, json=dict(usage=292, quota=10000))
    )
    result = client.account.quota()
    assert result == dict(usage=292, quota=10000)
