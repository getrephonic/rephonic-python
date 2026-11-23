---
name: rephonic-find-similar-podcasts
description: Find podcasts that share listeners with a podcast, e.g. to find more shows to pitch. Use when a user asks for "podcasts like X", "similar to Y", shared-audience analysis, or wants to discover shows related to a seed podcast.
---

# Find similar podcasts

Rephonic has two sources of similar podcasts, and both are based on shared listeners:

- `rephonic podcasts get <id>` returns `.podcast.similar`, which lists the closest matches to the seed with their listener estimates. They are ranked by `position`, and 1 is the most similar.
- `rephonic podcasts similar-graph <id>` returns the audience graph as `nodes` and `links`. It has the seed's similar podcasts and also the similar podcasts of each of those.

## Quick use

```bash
rephonic podcasts get huberman-lab \
  | jq '.podcast.similar | sort_by(.position) | .[] | {position, id, name, listeners: .downloads_per_episode}'
```

## Full workflow

### 1. Resolve seed podcast ID

If the user has an external identifier (Apple/iTunes ID, Spotify ID, YouTube channel ID, or RSS feed URL), resolve it with `podcasts lookup` instead of searching:

```bash
SEED=$(rephonic podcasts lookup --itunes-id 1545953110 | jq -r '.podcasts[0].id')
```

Otherwise, search by name:

```bash
SEED=$(rephonic search podcasts --query "huberman lab" | jq -r '.podcasts[0].id')
echo "$SEED"  # huberman-lab
```

### 2. Ranked direct matches

```bash
rephonic podcasts get "$SEED" | jq '
  .podcast.similar
  | sort_by(.position)
  | map({
      position,
      id,
      name,
      listeners: .downloads_per_episode,
      takes_guests: .guests.accepted,
      takes_sponsors: .sponsors.accepted
    })
'
```

Each entry is a short podcast stub (`id`, `name`, `publisher`, `genres`, `active`, `guests.accepted`, `sponsors.accepted`, `downloads_per_episode`, `weekly_downloads`, `position`). Pull `rephonic podcasts get <id>` for the full record.

### 3. Expand with the audience graph

```bash
rephonic podcasts similar-graph "$SEED" > graph.json
```

Each link has a `depth`. It is `0` for links to the seed's own similar podcasts and `1` for links to the similar podcasts of those. To find shows beyond the direct matches, drop the seed and its direct matches, then rank the remaining podcasts by how many direct matches link to each one:

```bash
jq --arg seed "$SEED" '
  .graph.links as $links
  | ([$links[] | select(.depth == 0) | .target] + [$seed]) as $known
  | [$links[] | select(.depth == 1) | .target | select(. as $t | $known | index($t) | not)]
  | group_by(.)
  | map({id: .[0], shared_with_direct_matches: length})
  | sort_by(-.shared_with_direct_matches)
  | .[0:20]
' graph.json > second_hop.json
```

### 4. Get listener counts

Graph nodes carry only `id`, `name`, `publisher`, `itunes_id`, artwork and `description`. For listener counts, fetch each podcast:

```bash
jq -r '.[].id' second_hop.json | while read pid; do
  rephonic podcasts get "$pid" \
    | jq '{id: .podcast.id, name: .podcast.name, listeners: .podcast.downloads_per_episode}'
done
```

## Graph response shape

```json
{
  "graph": {
    "nodes": [
      {"id": "huberman-lab", "name": "Huberman Lab", "publisher": "Scicomm Media", "itunes_id": 1545953110},
      {"id": "the-peter-attia-drive", "name": "The Peter Attia Drive", "publisher": "Peter Attia, MD", "itunes_id": 1400828889}
    ],
    "links": [
      {"source": "huberman-lab", "target": "the-peter-attia-drive", "depth": 0},
      {"source": "the-peter-attia-drive", "target": "foundmyfitness", "depth": 1}
    ]
  }
}
```

Links point from a podcast to one of its similar podcasts. Links carry no strength score, so for a ranking use `.podcast.similar[].position` (direct matches) or count shared links (second hop) as above.

## Edge cases

- A small podcast can have an empty graph when Rephonic doesn't have enough listener data to measure the overlap.
- If the seed isn't found, Rephonic returns 400 rather than 404, and the CLI exits 1. Look for "not found" or "unknown" in the error on stderr.
- `similar` stubs can have `null` listener and `accepted` fields for shows with little data.
