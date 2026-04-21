"""Grab the full transcript for a podcast's latest episode."""

import os

from rephonic import Rephonic


def main():
    client = Rephonic(api_key=os.environ["REPHONIC_API_KEY"])

    podcast = client.podcasts.get("huberman-lab")
    latest = podcast["podcast"]["latest_episode"]
    print(f"Latest episode: {latest['title']}")

    transcript = client.episodes.transcript(latest["id"])
    speakers = transcript["transcript"].get("speakers") or {}
    for segment in transcript["transcript"]["segments"][:5]:
        name = speakers.get(str(segment["speaker"]), f"Speaker {segment['speaker']}")
        print(f"[{segment['start'] // 1000:5}s] {name}: {segment['text']}")


if __name__ == "__main__":
    main()
