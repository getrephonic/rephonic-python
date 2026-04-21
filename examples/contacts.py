"""Build a media list of verified email contacts for a set of podcasts."""

import os

from rephonic import Rephonic


def main():
    client = Rephonic(api_key=os.environ["REPHONIC_API_KEY"])

    podcast_ids = ["huberman-lab", "the-daily", "lex-fridman-podcast"]

    for podcast_id in podcast_ids:
        response = client.podcasts.contacts(podcast_id)
        for contact in response["contacts"]["email"]:
            if contact["warning"] or contact["downvotes"] > contact["upvotes"]:
                continue
            name = contact.get("full_name") or "(unknown)"
            verified = "verified" if contact["concierge"] else "unverified"
            print(f"{podcast_id}: {name} <{contact['email']}> ({contact['category']}, {verified})")


if __name__ == "__main__":
    main()
