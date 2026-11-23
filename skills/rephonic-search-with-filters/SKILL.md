---
name: rephonic-search-with-filters
description: Search podcasts and episodes on Rephonic using JSON filter objects passed to --filters. Use when a user wants to find podcasts by listener count, country, category, language, founding year, professions, interests, or any other structured criteria. Also use when filter-syntax errors come up or when the user needs to look up IDs for category/country/language fields.
---

# Search Rephonic with filters

`rephonic search podcasts` and `rephonic search episodes` take a `--filters` option. Its value is a JSON object, passed as a string, with one key per field.

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
| `any` | `{"categories": {"any": [1482, 1406]}}` | Field has at least one of these values |
| `in` | `{"locations": {"in": ["us", "gb"]}}` | Field has every one of these values |

Rephonic's `in` works differently from SQL's `IN`. It matches only podcasts that have every listed value. To match podcasts that have at least one of the values, use `any`.

## Common fields

| Field | What it filters on |
|---|---|
| `listeners` | Downloads per episode |
| `active` | Whether the podcast is still publishing |
| `categories` | Category IDs, listed by `rephonic common categories` |
| `locations` | ISO country codes, listed by `rephonic common countries` |
| `languages` | ISO language codes |
| `professions` | Listener professions, listed by `rephonic common professions` |
| `interests` | Listener interests, listed by `rephonic common interests` |
| `founded` | Unix time in seconds, e.g. `{"gte": 1517270400}` means founded on or after 2018-01-30 |

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
  | jq '.podcasts[] | {id, name, downloads_per_episode}'
```

## Episode search

`rephonic search episodes` takes the same filters. `--threshold 604800` limits the results to episodes published in the last 604,800 seconds (7 days). To watch for new mentions of a brand, run a search like this on a schedule:

```bash
rephonic search episodes \
  --query "openai" \
  --threshold 604800 \
  | jq '.episodes[] | {podcast_id: .podcast.id, title, published}'
```

Max threshold is 1,209,600 seconds (14 days).

## Looking up IDs

Look up valid values for `categories`, `locations`, `languages`, `professions` and `interests` before you filter on them:

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

Check `.more` in the response to know when to stop. Max `per_page` is 100.

## Alternative filter forms

`--filters` also accepts the raw DSL string (legacy) or a JSON list of clauses:

```bash
# Raw DSL (what the API receives after encoding)
rephonic search podcasts --filters 'listeners:gte:5000,active:is:true'

# JSON list of raw clauses
rephonic search podcasts --filters '["listeners:gte:5000", "active:is:true"]'
```

The raw string form is there for filters you already have in that encoding, e.g. copied from another tool. In the JSON object form the CLI escapes values for you and you don't need to know the encoding.

## Edge cases

- In the JSON object form, the CLI escapes the reserved characters `-`, `,`, `:` and `\` in string values for you, so you can pass a value such as `"Harley-Davidson"` unchanged.
- Empty filter values like `{"categories": {"any": []}}` raise a 400. Omit the filter entirely instead.
- Mixing `any` and `in` on the same field is not supported. Pick one.
