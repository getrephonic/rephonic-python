---
name: rephonic-enrich-with-contacts
description: Pull email contacts, contact pages, and social accounts for a set of podcasts. Use when a user wants to build a media list, pitch guests, pitch sponsorships, enrich a CRM with podcast contact info, do outreach to podcast hosts, or any variation of "find the email for these shows".
---

# Enrich podcasts with contacts

The canonical outreach workflow: find podcasts, pull contacts, shape into a pitch list.

## The three-step pattern

1. Find candidate podcasts using search + filters.
2. Pull contacts for each podcast ID.
3. Shape into the format your CRM or email tool wants.

## Step 1: Find candidates

```bash
rephonic search podcasts \
  --query "startup" \
  --filters '{"listeners": {"gte": 5000}, "active": true, "locations": {"any": ["us"]}}' \
  --per-page 50 \
  | jq -r '.podcasts[].id' > podcast_ids.txt
```

## Step 2: Pull contacts

For a single podcast:

```bash
rephonic podcasts contacts the-daily
```

Response shape:

```json
{
  "contacts": {
    "email": [
      {
        "address": "host@example.com",
        "concierge": false,
        "warning": null,
        "upvotes": 12,
        "downvotes": 1
      }
    ],
    "page": ["https://example.com/contact"],
    "social": [...]
  }
}
```

Quality signals:

- `concierge: true` = verified by Rephonic staff, highest quality
- `warning` = known issue (e.g. "bounced recently")
- `upvotes` / `downvotes` = community signal

For a batch, loop over the IDs file:

```bash
while IFS= read -r pid; do
  rephonic podcasts contacts "$pid" | jq --arg pid "$pid" '{podcast_id: $pid, contacts: .contacts}'
done < podcast_ids.txt > contacts.jsonl
```

## Step 3: Shape

Pick the best email per podcast and flatten to a pitch list:

```bash
jq -s '
  map({
    podcast_id,
    email: (.contacts.email
             | map(select(.warning == null))
             | sort_by(-((.upvotes // 0) - (.downvotes // 0)))
             | first
             | .address),
    contact_page: (.contacts.page[0] // null)
  })
' contacts.jsonl > pitch_list.json
```

## Common additions

- **Listener count**: join with `rephonic podcasts get <id>` to pull `.podcast.downloads_per_episode`.
- **Hosts and guests**: `rephonic podcasts people <id>` returns structured host info with their own contacts.
- **Demographics**: `rephonic podcasts demographics <id>` to tailor the pitch by audience age, profession, income, etc.

## Parallelize for speed

For >100 podcasts, shell loops are slow. Use the Python SDK's async client to fan out:

```python
import asyncio
from rephonic import AsyncRephonic

async def main():
    async with AsyncRephonic() as c:
        ids = [line.strip() for line in open("podcast_ids.txt") if line.strip()]
        contacts = await asyncio.gather(
            *(c.podcasts.contacts(pid) for pid in ids),
            return_exceptions=True,
        )
        for pid, res in zip(ids, contacts):
            if isinstance(res, Exception):
                print(f"{pid}: {res}")
            else:
                print({"podcast_id": pid, "contacts": res["contacts"]})

asyncio.run(main())
```

## Edge cases

- Not every podcast has a public email. `.contacts.email` may be empty. Fall back to `.contacts.page` (contact form URL) or `.contacts.social`.
- Rephonic returns 400 (not 404) for "podcast not found". CLI exits 1. Check stderr for the message.
- Rate limit: default quota is 10k requests/month. Batching tight loops eats quota. Check with `rephonic account quota`.
- Emails flagged with `warning` should generally be skipped unless your tool tolerates bounces.
