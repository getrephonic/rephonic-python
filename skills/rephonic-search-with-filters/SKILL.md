---
name: rephonic-search-with-filters
description: Search podcasts and episodes on Rephonic using Stripe-style filter dicts. Use when a user wants to find podcasts by listener count, country, category, language, founding year, professions, interests, or any other structured criteria. Also use when filter-syntax errors come up or when the user needs to look up IDs for category/country/language fields.
---

# Search Rephonic with filters

Rephonic's search supports rich filtering via a Stripe-style JSON dict passed as a string to `--filters`.

## Basic example

```bash
rephonic search podcasts \
  --query "marketing" \
  --filters '{"listeners": {"gte": 10000}, "active": true}'
```

## Operators

| Operator | Shape | Meaning |
|---|---|---|
| `gte` / `lte` | `{"listeners": {"gte": 5000}}` | Numeric threshold |
| `is` (implicit) | `{"active": true}` | Boolean, pass the bool directly |
| `any` | `{"categories": {"any": [1482, 1406]}}` | Field contains ANY of these values (OR, union) |
| `in` | `{"locations": {"in": ["us", "gb"]}}` | Field contains ALL of these values (AND, intersection) |

**Gotcha**: Rephonic's `in` means AND / intersection, not SQL-style set membership. Use `any` for OR semantics. This is the single most common filter mistake.

## Common fields

- `listeners` — downloads per episode
- `active` — still publishing
- `categories` — list of category IDs (look up via `rephonic common categories`)
- `locations` — ISO country codes (look up via `rephonic common countries`)
- `languages` — ISO language codes
- `professions` / `interests` — ID lookups via `rephonic common professions` / `interests`
- `founded` — unix seconds, e.g. `{"gte": 1517270400}` = "after 2018-01-30"

Full list: https://rephonic.com/developers/search-filters

## Multi-filter example

Active US marketing podcasts with >10k listeners, targeting Doctor or Lawyer audiences:

```bash
rephonic search podcasts \
  --query "marketing" \
  --filters '{
    "listeners": {"gte": 10000},
    "active": true,
    "locations": {"any": ["us"]},
    "professions": {"any": ["Doctor", "Lawyer"]}
  }' \
  --per-page 25 \
  | jq '.podcasts[] | {id, name, listeners_per_episode}'
```

## Episode search

Same filter syntax applies to `rephonic search episodes`. Add `--threshold 604800` (seconds) to restrict to recent episodes for near-realtime brand monitoring:

```bash
rephonic search episodes \
  --query "openai" \
  --threshold 604800 \
  | jq '.episodes[] | {podcast_id, title, published_at}'
```

Max threshold is 1,209,600 seconds (14 days).

## Looking up IDs

`categories`, `countries`, `languages`, `professions`, `interests` all use IDs. Look them up first:

```bash
rephonic common categories | jq '.categories[] | select(.name | contains("Business")) | {id, name}'
rephonic common countries | jq '.countries[] | select(.name == "United States")'
rephonic common professions --query doctor
```

## Pagination

```bash
rephonic search podcasts --query "ai" --per-page 50 --page 1
rephonic search podcasts --query "ai" --per-page 50 --page 2
```

Check `.more` in the response to know when to stop. Max `per_page` is 50 for podcasts, 25 for episodes.

## Alternative filter forms

`--filters` also accepts the raw DSL string (legacy) or a JSON list of clauses:

```bash
# Raw DSL (what the API receives after encoding)
rephonic search podcasts --filters 'listeners:gte:5000,active:is:true'

# JSON list of raw clauses
rephonic search podcasts --filters '["listeners:gte:5000", "active:is:true"]'
```

The dict form is almost always easier. Use the DSL form only if you already have encoded filters from somewhere else.

## Edge cases

- Reserved characters in string values (`-`, `,`, `:`, `\`) are escaped automatically. `"Harley-Davidson"` just works.
- Empty filter values like `{"categories": {"any": []}}` raise a 400. Omit the filter entirely instead.
- Mixing `any` and `in` on the same field is not supported. Pick one.
