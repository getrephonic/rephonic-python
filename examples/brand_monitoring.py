"""Monitor podcast episodes published in the last 24 hours for a brand mention."""

import os

from rephonic import Rephonic


def main():
    client = Rephonic(api_key=os.environ["REPHONIC_API_KEY"])

    one_day = 24 * 60 * 60
    results = client.search.episodes(
        query='"Acme Corporation" OR "acme.com"',
        threshold=one_day,
        highlight=True,
        per_page=50,
    )
    for episode in results["episodes"]:
        print(f"{episode['podcast']['name']}: {episode['title']}")
        if episode.get("highlight"):
            print(f"  -> {episode['highlight']}")


if __name__ == "__main__":
    main()
