"""Fan out concurrent API calls using AsyncRephonic.

Useful when you need data for many podcasts at once (media lists, enrichment
pipelines, bulk reporting) — the total time is ~max(individual call time)
rather than the sum.
"""

import asyncio
import os

from rephonic import AsyncRephonic


async def main():
    podcast_ids = [
        "huberman-lab",
        "the-daily",
        "lex-fridman-podcast",
        "the-joe-rogan-experience",
        "this-american-life",
    ]

    async with AsyncRephonic(api_key=os.environ["REPHONIC_API_KEY"]) as client:
        demographics, contacts = await asyncio.gather(
            asyncio.gather(*(client.podcasts.demographics(i) for i in podcast_ids)),
            asyncio.gather(*(client.podcasts.contacts(i) for i in podcast_ids)),
        )

    for podcast_id, demo, cts in zip(podcast_ids, demographics, contacts):
        income = demo["demographics"]["household_incomes"]
        emails = len(cts["contacts"]["email"])
        print(
            f"{podcast_id}: income ${income['lower']:,}-${income['upper']:,}, "
            f"{emails} email contact(s)"
        )


if __name__ == "__main__":
    asyncio.run(main())
