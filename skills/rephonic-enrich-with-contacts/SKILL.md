---
name: rephonic-enrich-with-contacts
description: Pull email contacts, contact pages, and social accounts for a set of podcasts. Use when a user wants to build a media list, pitch guests, pitch sponsorships, enrich a CRM with podcast contact info, do outreach to podcast hosts, or any variation of "find the email for these shows".
---

# Enrich podcasts with contacts

The commands below use the `rephonic` CLI and `jq`.

## 1. Find podcasts to pitch

Search with filters and save the podcast IDs to a file:

```bash
rephonic search podcasts \
  --query "startup" \
  --filters '{"listeners": {"gte": 5000}, "active": true, "locations": {"any": ["us"]}}' \
  --per-page 50 \
  | jq -r '.podcasts[].id' > podcast_ids.txt
```

## 2. Pull their contacts

For a single podcast:

```bash
rephonic podcasts contacts the-daily
```

The response looks like this, with emails and contact pages together in one `contacts` list, ranked best first:

```json
{
  "contacts": [
    {
      "medium": "email",
      "email": "host@example.com",
      "full_name": "Jane Host",
      "role": "Host",
      "warning": false,
      "verification_status": "valid",
      "badges": ["best", "pitch_guests"],
      "upvotes": 12,
      "downvotes": 1
    },
    {
      "medium": "page",
      "url": "https://example.com/contact",
      "role": "Contact Page",
      "badges": []
    }
  ],
  "social": [...]
}
```

These fields help you pick which contact to use:

- In `badges`, `best` marks the contact we recommend reaching out to first, which can be an email or a page. `pitch_guests` and `pitch_sponsors` mark the best way to pitch a guest or ask about advertising. `replies_to_pitches` marks an email that has answered pitches sent through Rephonic.
- `verification_status` says whether email to the address is likely to be delivered. It is `valid`, `catch-all`, `risky`, `unknown`, or `null` when the address hasn't been checked. Addresses found to be invalid are left out.
- `warning: true` means the address is probably not a real inbox, e.g. a hosting provider's masked address.
- `upvotes` and `downvotes` count the Rephonic users who marked the contact as good or bad.

For a batch, loop over the IDs file:

```bash
while IFS= read -r pid; do
  rephonic podcasts contacts "$pid" | jq --arg pid "$pid" '{podcast_id: $pid, contacts: .contacts}'
done < podcast_ids.txt > contacts.jsonl
```

## 3. Build the pitch list

This keeps the top-ranked email and the first contact page for each podcast:

```bash
jq -s '
  map({
    podcast_id,
    email: ([.contacts[] | select(.medium == "email" and (.warning | not))]
             | first
             | .email),
    contact_page: ([.contacts[] | select(.medium == "page")] | first | .url)
  })
' contacts.jsonl > pitch_list.json
```

## Pitch routes from the podcast itself

`rephonic podcasts get <id>` carries an `outreach` block on `.podcast.guests` and `.podcast.sponsors` saying how to pitch a guest or buy ads on that show:

```bash
rephonic podcasts get huberman-lab | jq '.podcast.guests.outreach'
```

```json
{
  "pitchable": true,
  "instructions": "Submit guest suggestions via the form on the show website.",
  "contacts": [
    {"medium": "page", "url": "https://example.com/guest-form", "role": "Guest Submissions", "badges": ["pitch_guests"]}
  ]
}
```

- `pitchable: false` means the show has said it doesn't take these pitches. `contacts` is then empty. Skip the show.
- `contacts` uses the same shape as `rephonic podcasts contacts` (without the vote counts), best first.
- `outreach` is `null` when we have no route for that purpose. When neither has one, `guests.outreach` falls back to the show's top general contacts, with `instructions: null`.
- `.podcast.guests.accepted` / `.podcast.sponsors.accepted` say whether the show takes guests / sponsors at all.

## Other data to add to the list

- The listener estimate is `.podcast.downloads_per_episode` from `rephonic podcasts get <id>`.
- `rephonic podcasts people <id>` returns the hosts and crew (e.g. producers, bookers and ad sales), each with their own contacts. Every person has a `kind` and a `role`, and `is_lead: true` marks the current host or hosts who front the show.
- `.podcast.entities` from `rephonic podcasts get <id>` lists the production company, network, ad-sales agency or talent agency behind the show. Email contacts also have `person` and `entity` fields that say who the address belongs to.
- `rephonic podcasts demographics <id>` returns estimated audience breakdowns, e.g. by age or income, which you can use to tailor the pitch.

## Edge cases

- Not every podcast has a public email. `.contacts` may hold only pages (`medium == "page"`, contact form URL) or be empty. Fall back to `.social`.
- Rephonic returns 400, not 404, when a podcast isn't found, and the CLI exits 1. The message is on stderr.
- Every call counts against your monthly quota, which is 10,000 requests by default. A large batch can use up a lot of it, so check `rephonic account quota` first.
- Skip emails with `warning: true` unless you don't mind some bounces.
