import httpx
import respx


@respx.mock
def test_iter_podcasts_follows_pages(client):
    respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        side_effect=[
            httpx.Response(
                200,
                json=dict(podcasts=[dict(id="a"), dict(id="b")], page=1, per_page=2, more=True),
            ),
            httpx.Response(
                200,
                json=dict(podcasts=[dict(id="c"), dict(id="d")], page=2, per_page=2, more=True),
            ),
            httpx.Response(
                200,
                json=dict(podcasts=[dict(id="e")], page=3, per_page=2, more=False),
            ),
        ]
    )
    ids = [p["id"] for p in client.search.iter_podcasts(per_page=2)]
    assert ids == ["a", "b", "c", "d", "e"]


@respx.mock
def test_iter_podcasts_respects_limit(client):
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
    ids = [p["id"] for p in client.search.iter_podcasts(per_page=50, limit=3)]
    assert ids == ["0", "1", "2"]


@respx.mock
def test_iter_episodes_short_page_stops(client):
    respx.get("https://api.rephonic.com/api/search/episodes/").mock(
        return_value=httpx.Response(
            200,
            json=dict(episodes=[dict(id="a"), dict(id="b")], page=1, per_page=50, more=False),
        )
    )
    ids = [e["id"] for e in client.search.iter_episodes(per_page=50)]
    assert ids == ["a", "b"]


@respx.mock
def test_iter_podcasts_follows_more_even_when_page_is_short(client):
    """If the server reports `more: True`, keep paging even if items < per_page."""
    respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        side_effect=[
            httpx.Response(
                200,
                json=dict(podcasts=[dict(id="a")], page=1, per_page=50, more=True),
            ),
            httpx.Response(
                200,
                json=dict(podcasts=[dict(id="b"), dict(id="c")], page=2, per_page=50, more=False),
            ),
        ]
    )
    ids = [p["id"] for p in client.search.iter_podcasts(per_page=50)]
    assert ids == ["a", "b", "c"]


@respx.mock
def test_iter_episodes_list_for_podcast(client):
    respx.get("https://api.rephonic.com/api/episodes/").mock(
        side_effect=[
            httpx.Response(
                200,
                json=dict(
                    episodes=[dict(id=str(i)) for i in range(25)],
                    page=1,
                    per_page=25,
                    total_count=27,
                ),
            ),
            httpx.Response(
                200,
                json=dict(
                    episodes=[dict(id="25"), dict(id="26")],
                    page=2,
                    per_page=25,
                    total_count=27,
                ),
            ),
        ]
    )
    ids = [e["id"] for e in client.episodes.iter_list(podcast_id="x", per_page=25)]
    assert ids == [str(i) for i in range(27)]
