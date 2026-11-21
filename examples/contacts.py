"""Build a media list of verified email contacts for a set of podcasts."""

import os

from rephonic import Rephonic


def main():
    client = Rephonic(api_key=os.environ["REPHONIC_API_KEY"])

    podcast_ids = ["huberman-lab", "the-daily", "lex-fridman-podcast"]

    for podcast_id in podcast_ids:
        response = client.podcasts.contacts(podcast_id)
        for contact in response["contacts"]:
            if contact["medium"] != "email":
                continue
            if contact["warning"] or contact["downvotes"] > contact["upvotes"]:
                continue
            name = contact["full_name"] or "(unknown)"
            status = contact["verification_status"] or "unchecked"
            best = " [recommended]" if "best" in contact["badges"] else ""
            print(f"{podcast_id}: {name} <{contact['email']}> ({contact['role']}, {status}){best}")


if __name__ == "__main__":
    main()
