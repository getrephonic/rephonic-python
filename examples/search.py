"""Search for podcasts matching a query with filters applied."""

import os

from rephonic import Rephonic


def main():
    client = Rephonic(api_key=os.environ["REPHONIC_API_KEY"])

    # One page at a time.
    page = client.search.podcasts(
        query="artificial intelligence",
        mode="topics",
        filters="listeners:gte:10000,active:is:true",
        per_page=10,
    )
    for podcast in page["podcasts"]:
        print(f"{podcast['name']} - {podcast['downloads_per_episode']:,} listeners/ep")

    print()
    print("--- Top 5 episodes mentioning 'climate change' ---")
    episodes = client.search.episodes(query="climate change", per_page=5)
    for episode in episodes["episodes"]:
        print(f"{episode['podcast']['name']}: {episode['title']}")


if __name__ == "__main__":
    main()
