"""Smoke tests for the Rephonic CLI."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from rephonic import Rephonic
from rephonic._cli import app
from rephonic._version import __version__


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPHONIC_API_KEY", "test-key")


@pytest.fixture
def fast_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable retries so 429/5xx tests finish fast."""
    monkeypatch.setattr("rephonic._cli._make_client", lambda: Rephonic(max_retries=0))


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_help_with_no_args(runner: CliRunner) -> None:
    result = runner.invoke(app, [])
    assert result.exit_code != 0
    assert "Rephonic" in (result.stdout + result.stderr)


def test_missing_api_key(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REPHONIC_API_KEY", raising=False)
    result = runner.invoke(app, ["account", "quota"])
    assert result.exit_code == 4
    payload = json.loads(result.stderr)
    assert payload["error"]["type"] == "AuthenticationError"
    assert "REPHONIC_API_KEY" in payload["error"]["message"]


@respx.mock
def test_account_quota_success(runner: CliRunner, api_key: None) -> None:
    respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(200, json=dict(usage=42, quota=10000))
    )
    result = runner.invoke(app, ["account", "quota"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"usage": 42, "quota": 10000}


@respx.mock
def test_podcasts_get(runner: CliRunner, api_key: None) -> None:
    respx.get("https://api.rephonic.com/api/podcasts/huberman-lab/").mock(
        return_value=httpx.Response(
            200, json=dict(podcast=dict(id="huberman-lab", name="Huberman Lab"))
        )
    )
    result = runner.invoke(app, ["podcasts", "get", "huberman-lab"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["podcast"]["id"] == "huberman-lab"


@respx.mock
def test_search_with_json_filters(runner: CliRunner, api_key: None) -> None:
    route = respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        return_value=httpx.Response(200, json=dict(podcasts=[], more=False))
    )
    result = runner.invoke(
        app,
        [
            "search",
            "podcasts",
            "--query",
            "ai",
            "--filters",
            '{"listeners": {"gte": 5000}, "active": true}',
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert route.called
    params = route.calls.last.request.url.params
    assert params["query"] == "ai"
    encoded = params["filters"]
    assert "listeners:gte:5000" in encoded
    assert "active:is:true" in encoded


@respx.mock
def test_search_with_raw_dsl_filters(runner: CliRunner, api_key: None) -> None:
    route = respx.get("https://api.rephonic.com/api/search/podcasts/").mock(
        return_value=httpx.Response(200, json=dict(podcasts=[], more=False))
    )
    result = runner.invoke(
        app,
        ["search", "podcasts", "--filters", "listeners:gte:5000"],
    )
    assert result.exit_code == 0, result.stderr
    assert route.calls.last.request.url.params["filters"] == "listeners:gte:5000"


def test_invalid_json_filters(runner: CliRunner, api_key: None) -> None:
    result = runner.invoke(app, ["search", "podcasts", "--filters", "{not valid json"])
    assert result.exit_code == 2  # typer BadParameter


@respx.mock
def test_auth_error_exit_code(runner: CliRunner, api_key: None) -> None:
    respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(401, json=dict(error="Invalid API key."))
    )
    result = runner.invoke(app, ["account", "quota"])
    assert result.exit_code == 4
    payload = json.loads(result.stderr)
    assert payload["error"]["type"] == "AuthenticationError"
    assert payload["error"]["status_code"] == 401


@respx.mock
def test_server_error_exit_code(runner: CliRunner, api_key: None, fast_client: None) -> None:
    respx.get("https://api.rephonic.com/api/accounts/quota/").mock(
        return_value=httpx.Response(500, json=dict(error="boom"))
    )
    result = runner.invoke(app, ["account", "quota"])
    assert result.exit_code == 5
    payload = json.loads(result.stderr)
    assert payload["error"]["type"] == "InternalServerError"
    assert payload["error"]["status_code"] == 500


@respx.mock
def test_bad_request_exit_code(runner: CliRunner, api_key: None) -> None:
    respx.get("https://api.rephonic.com/api/podcasts/does-not-exist/").mock(
        return_value=httpx.Response(400, json=dict(error="Podcast not found."))
    )
    result = runner.invoke(app, ["podcasts", "get", "does-not-exist"])
    assert result.exit_code == 1
    payload = json.loads(result.stderr)
    assert payload["error"]["type"] == "BadRequestError"
    assert payload["error"]["status_code"] == 400
    assert "not found" in payload["error"]["message"].lower()


@respx.mock
def test_charts_rankings_path_params(runner: CliRunner, api_key: None) -> None:
    route = respx.get("https://api.rephonic.com/api/charts/apple/us/all/").mock(
        return_value=httpx.Response(200, json=dict(rankings=[]))
    )
    result = runner.invoke(
        app,
        ["charts", "rankings", "apple", "--country", "us", "--category", "all"],
    )
    assert result.exit_code == 0, result.stderr
    assert route.called
