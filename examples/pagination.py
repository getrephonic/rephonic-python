"""Iterate across paginated results with ``iter_*`` helpers."""

import os

from rephonic import Rephonic


def main():
    client = Rephonic(api_key=os.environ["REPHONIC_API_KEY"])

    # Pull the first 500 podcasts matching a filter, paging transparently.
    podcasts = client.search.iter_podcasts(
        filters="categories:in:1482,listeners:gte:1000",
        per_page=100,
        limit=500,
    )
    for i, podcast in enumerate(podcasts, start=1):
        print(f"{i:3}. {podcast['name']}")


if __name__ == "__main__":
    main()
