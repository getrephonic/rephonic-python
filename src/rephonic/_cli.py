"""Command-line interface for the Rephonic podcast API.

Entry point: ``rephonic`` (installed via ``[project.scripts]``).

Emits JSON on stdout for every command; structured JSON errors on stderr.
Authentication comes from the ``REPHONIC_API_KEY`` environment variable.

Exit codes:
    0  success
    1  other error (API, network, client-side)
    2  usage error (bad flags, handled by typer)
    4  authentication error (missing / invalid API key)
    5  server error (Rephonic API 5xx)
"""

import json
import sys
from typing import Any, Callable, Dict, Optional

import typer

from ._client import Rephonic
from ._exceptions import (
    APIStatusError,
    AuthenticationError,
    InternalServerError,
    RephonicError,
)
from ._version import __version__

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_AUTH = 4
EXIT_SERVER = 5


def _make_typer(help_text: str, epilog: Optional[str] = None) -> typer.Typer:
    return typer.Typer(
        help=help_text,
        epilog=epilog,
        no_args_is_help=True,
        add_completion=False,
        rich_markup_mode=None,
        context_settings=dict(help_option_names=["-h", "--help"]),
    )


ROOT_EPILOG = (
    "Output is JSON on stdout; errors are JSON on stderr. "
    "Pipe through `jq` to extract fields.\n"
    "\n"
    "Auth: set REPHONIC_API_KEY in the environment. "
    "Get an API key at https://rephonic.com/developers.\n"
    "\n"
    "Exit codes: 0 success, 1 API or network error, 2 usage error, "
    "4 authentication error, 5 server error.\n"
    "\n"
    "Docs: https://rephonic.com/developers. "
    "LLM-friendly reference: https://rephonic.com/llms-full.txt."
)


app = _make_typer("Rephonic podcast intelligence API from the command line.", epilog=ROOT_EPILOG)
search_app = _make_typer("Search podcasts and episodes.")
podcasts_app = _make_typer("Look up podcast metadata, people, demographics, contacts, and more.")
episodes_app = _make_typer("List, look up, and transcribe episodes.")
charts_app = _make_typer("Daily chart rankings from Apple, Spotify, and YouTube.")
common_app = _make_typer("Reference data for search filters.")
account_app = _make_typer("Account quota and usage.")

app.add_typer(search_app, name="search")
app.add_typer(podcasts_app, name="podcasts")
app.add_typer(episodes_app, name="episodes")
app.add_typer(charts_app, name="charts")
app.add_typer(common_app, name="common")
app.add_typer(account_app, name="account")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def _root(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Print version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Rephonic podcast intelligence API."""


def _make_client() -> Rephonic:
    """Instantiate a ``Rephonic`` client. Tests can monkey-patch this."""
    return Rephonic()


def _emit_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2, sort_keys=False)
    sys.stdout.write("\n")


def _emit_error(
    message: str,
    *,
    error_type: str,
    status_code: Optional[int] = None,
    body: Optional[Any] = None,
) -> None:
    payload: Dict[str, Any] = dict(error=dict(type=error_type, message=message))
    if status_code is not None:
        payload["error"]["status_code"] = status_code
    if body is not None:
        payload["error"]["body"] = body
    json.dump(payload, sys.stderr, ensure_ascii=False, indent=2, sort_keys=False)
    sys.stderr.write("\n")


def _parse_filters(raw: Optional[str]) -> Any:
    """Accept a JSON dict, JSON list, or raw DSL string for --filters."""
    if raw is None:
        return None
    stripped = raw.lstrip()
    if stripped.startswith(("{", "[")):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise typer.BadParameter(f"--filters is not valid JSON: {exc}") from exc
    return raw


def _run(fn: Callable[[Rephonic], Any]) -> None:
    """Execute a resource call, emit JSON on success, structured error + exit otherwise."""
    try:
        client = _make_client()
    except ValueError as exc:
        _emit_error(str(exc), error_type="AuthenticationError")
        raise typer.Exit(code=EXIT_AUTH) from None

    try:
        try:
            result = fn(client)
        finally:
            client.close()
    except AuthenticationError as exc:
        _emit_error(
            exc.message,
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            body=exc.body,
        )
        raise typer.Exit(code=EXIT_AUTH) from None
    except InternalServerError as exc:
        _emit_error(
            exc.message,
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            body=exc.body,
        )
        raise typer.Exit(code=EXIT_SERVER) from None
    except APIStatusError as exc:
        _emit_error(
            exc.message,
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            body=exc.body,
        )
        raise typer.Exit(code=EXIT_ERROR) from None
    except RephonicError as exc:
        _emit_error(str(exc), error_type=type(exc).__name__)
        raise typer.Exit(code=EXIT_ERROR) from None

    _emit_json(result)


# --- search --------------------------------------------------------------


@search_app.command("podcasts")
def search_podcasts(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query."),
    mode: Optional[str] = typer.Option(
        None, "--mode", help='"topics" (default), "titles", or "publishers".'
    ),
    per_page: Optional[int] = typer.Option(None, "--per-page"),
    page: Optional[int] = typer.Option(None, "--page"),
    filters: Optional[str] = typer.Option(
        None,
        "--filters",
        help='Stripe-style JSON dict (\'{"listeners":{"gte":5000}}\'), '
        "JSON list, or legacy DSL string.",
    ),
) -> None:
    """Search for podcasts by topic, title, or publisher.

    Example: rephonic search podcasts --query "marketing" --filters '{"listeners":{"gte":10000},"active":true}'
    """
    parsed = _parse_filters(filters)
    _run(
        lambda c: c.search.podcasts(
            query=query, mode=mode, per_page=per_page, page=page, filters=parsed
        )
    )


@search_app.command("episodes")
def search_episodes(
    query: Optional[str] = typer.Option(None, "--query", "-q"),
    per_page: Optional[int] = typer.Option(None, "--per-page"),
    page: Optional[int] = typer.Option(None, "--page"),
    filters: Optional[str] = typer.Option(None, "--filters"),
    highlight: Optional[bool] = typer.Option(None, "--highlight/--no-highlight"),
    podcast_id: Optional[str] = typer.Option(None, "--podcast-id"),
    threshold: Optional[int] = typer.Option(
        None,
        "--threshold",
        help="Restrict to episodes published in the last N seconds (max 1,209,600).",
    ),
) -> None:
    """Full-text search across episode titles, show notes, and transcripts.

    Example: rephonic search episodes --query "openai" --threshold 604800
    """
    parsed = _parse_filters(filters)
    _run(
        lambda c: c.search.episodes(
            query=query,
            per_page=per_page,
            page=page,
            filters=parsed,
            highlight=highlight,
            podcast_id=podcast_id,
            threshold=threshold,
        )
    )


@search_app.command("autocomplete")
def search_autocomplete(
    mode: str = typer.Option(
        ..., "--mode", help='"topics", "titles", "publishers", or "episodes".'
    ),
    query: str = typer.Option(..., "--query", "-q"),
) -> None:
    """Suggest keywords and matching podcasts for a partial query."""
    _run(lambda c: c.search.autocomplete(mode=mode, query=query))


# --- podcasts ------------------------------------------------------------


@podcasts_app.command("get")
def podcasts_get(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
) -> None:
    """Full metadata, chart rankings, YouTube channel, similar podcasts, latest episode.

    Example: rephonic podcasts get huberman-lab
    """
    _run(lambda c: c.podcasts.get(podcast_id))


@podcasts_app.command("people")
def podcasts_people(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
) -> None:
    """Hosts and recent guests with contacts and social accounts."""
    _run(lambda c: c.podcasts.people(podcast_id))


@podcasts_app.command("demographics")
def podcasts_demographics(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
) -> None:
    """Estimated listener demographics: age, gender, education, income, interests, location."""
    _run(lambda c: c.podcasts.demographics(podcast_id))


@podcasts_app.command("promotions")
def podcasts_promotions(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
) -> None:
    """Sponsors and cross-promotions with ad text, promo codes, and URLs."""
    _run(lambda c: c.podcasts.promotions(podcast_id))


@podcasts_app.command("contacts")
def podcasts_contacts(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
) -> None:
    """Email contacts, contact pages, and social accounts with quality signals.

    Example: rephonic podcasts contacts the-daily
    """
    _run(lambda c: c.podcasts.contacts(podcast_id))


@podcasts_app.command("social")
def podcasts_social(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
) -> None:
    """Social media accounts with follower and engagement metrics."""
    _run(lambda c: c.podcasts.social(podcast_id))


@podcasts_app.command("feedback")
def podcasts_feedback(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
) -> None:
    """Overall ratings across apps plus AI-generated summary insights."""
    _run(lambda c: c.podcasts.feedback(podcast_id))


@podcasts_app.command("reviews")
def podcasts_reviews(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
    platform: str = typer.Option(
        ...,
        "--platform",
        help='"all", "apple", "podchaser", "castbox", "audible", or "podaddict".',
    ),
) -> None:
    """Individual listener reviews in chronological order."""
    _run(lambda c: c.podcasts.reviews(podcast_id, platform=platform))


@podcasts_app.command("trends")
def podcasts_trends(
    podcast_ids: str = typer.Argument(
        ..., metavar="PODCAST_IDS", help="Single ID or comma-separated IDs (max 3)."
    ),
    metrics: str = typer.Option(
        ...,
        "--metrics",
        help='Comma-separated metrics (max 5): "downloads_per_episode", '
        '"social_reach", "spotify_followers".',
    ),
) -> None:
    """Historical time series for podcast metrics.

    Example: rephonic podcasts trends huberman-lab,lex-fridman-podcast --metrics downloads_per_episode,social_reach
    """
    _run(lambda c: c.podcasts.trends(podcast_ids, metrics=metrics))


@podcasts_app.command("similar-graph")
def podcasts_similar_graph(
    podcast_id: str = typer.Argument(..., metavar="PODCAST_ID"),
) -> None:
    """Shared-audience graph (nodes + links) of podcasts with overlapping listeners."""
    _run(lambda c: c.podcasts.similar_graph(podcast_id))


# --- episodes ------------------------------------------------------------


@episodes_app.command("list")
def episodes_list(
    podcast_id: str = typer.Option(..., "--podcast-id"),
    query: Optional[str] = typer.Option(None, "--query", "-q"),
    per_page: Optional[int] = typer.Option(None, "--per-page", help="Max 25."),
    page: Optional[int] = typer.Option(None, "--page"),
) -> None:
    """Every episode for a podcast in chronological order."""
    _run(
        lambda c: c.episodes.list(podcast_id=podcast_id, query=query, per_page=per_page, page=page)
    )


@episodes_app.command("get")
def episodes_get(
    episode_id: str = typer.Argument(..., metavar="EPISODE_ID"),
) -> None:
    """Full episode metadata including topics, guests, hosts, sponsors, key moments."""
    _run(lambda c: c.episodes.get(episode_id))


@episodes_app.command("transcript")
def episodes_transcript(
    episode_id: str = typer.Argument(..., metavar="EPISODE_ID"),
) -> None:
    """Timestamped transcript segments with speaker IDs (when available).

    Example: rephonic episodes transcript kzaca-huberman-lab-dr-brian-keating-charting-the-a
    """
    _run(lambda c: c.episodes.transcript(episode_id))


# --- charts --------------------------------------------------------------


@charts_app.command("index")
def charts_index(
    platform: str = typer.Argument(
        ..., metavar="PLATFORM", help='"apple", "spotify", or "youtube".'
    ),
) -> None:
    """Available countries and categories for a chart platform."""
    _run(lambda c: c.charts.index(platform))


@charts_app.command("rankings")
def charts_rankings(
    platform: str = typer.Argument(..., metavar="PLATFORM"),
    country: str = typer.Option(..., "--country"),
    category: str = typer.Option(..., "--category", help='Use "all" for the overall top chart.'),
) -> None:
    """Latest chart rankings for a platform + country + category.

    Example: rephonic charts rankings apple --country us --category all
    """
    _run(lambda c: c.charts.rankings(platform, country=country, category=category))


# --- common --------------------------------------------------------------


@common_app.command("categories")
def common_categories() -> None:
    """List every podcast category (IDs used with the ``categories`` filter)."""
    _run(lambda c: c.common.categories())


@common_app.command("countries")
def common_countries() -> None:
    """List every country (IDs used with the ``locations`` filter)."""
    _run(lambda c: c.common.countries())


@common_app.command("languages")
def common_languages() -> None:
    """List every language (codes used with the ``languages`` filter)."""
    _run(lambda c: c.common.languages())


@common_app.command("sponsors")
def common_sponsors(
    query: Optional[str] = typer.Option(None, "--query", "-q"),
) -> None:
    """Commonly seen sponsors, optionally filtered by name."""
    _run(lambda c: c.common.sponsors(query=query))


@common_app.command("professions")
def common_professions(
    query: Optional[str] = typer.Option(None, "--query", "-q"),
) -> None:
    """Common listener professions, optionally filtered by name."""
    _run(lambda c: c.common.professions(query=query))


@common_app.command("interests")
def common_interests(
    query: Optional[str] = typer.Option(None, "--query", "-q"),
) -> None:
    """Common listener interests, optionally filtered by name."""
    _run(lambda c: c.common.interests(query=query))


# --- account -------------------------------------------------------------


@account_app.command("quota")
def account_quota() -> None:
    """API request quota and usage for the current month.

    Example: rephonic account quota
    """
    _run(lambda c: c.account.quota())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
