---
name: rephonic-find-similar-podcasts
description: Find podcasts with overlapping audiences for guest pitching, media-list expansion, recommendation features, or competitive research. Use when a user asks for "podcasts like X", "similar to Y", shared-audience analysis, or wants to discover shows related to a seed podcast.
---

# Find similar podcasts

Rephonic's similar-graph endpoint returns a weighted graph of podcasts with overlapping listeners. Edge weight corresponds to audience-overlap strength.

## Quick use

```bash
rephonic podcasts similar-graph huberman-lab | jq '.graph.nodes[0:10]'
```

## Full workflow

### 1. Resolve seed podcast ID

If the user gives a name, look it up:

```bash
SEED=$(rephonic search podcasts --query "huberman lab" | jq -r '.podcasts[0].id')
echo "$SEED"  # huberman-lab
```

### 2. Pull the graph

```bash
rephonic podcasts similar-graph "$SEED" > graph.json
```

### 3. Rank by edge weight

Extract direct neighbours of the seed and sort by weight:

```bash
jq --arg seed "$SEED" '
  .graph.links
  | map(select(.source == $seed or .target == $seed))
  | sort_by(-.weight)
  | .[0:20]
  | map({
      other: (if .source == $seed then .target else .source end),
      weight
    })
' graph.json
```

### 4. Hydrate with metadata

```bash
jq -r --arg seed "$SEED" '
  .graph.links
  | map(select(.source == $seed or .target == $seed))
  | sort_by(-.weight)
  | .[0:10]
  | .[] | (if .source == $seed then .target else .source end)
' graph.json | while read pid; do
  rephonic podcasts get "$pid" \
    | jq '{id: .podcast.id, name: .podcast.name, listeners: .podcast.downloads_per_episode}'
done
```

## Response shape

```json
{
  "graph": {
    "nodes": [
      {"id": "huberman-lab", "name": "Huberman Lab"},
      {"id": "lex-fridman-podcast", "name": "Lex Fridman Podcast"}
    ],
    "links": [
      {"source": "huberman-lab", "target": "lex-fridman-podcast", "weight": 0.42}
    ]
  }
}
```

The graph is undirected. `{source: A, target: B}` and `{source: B, target: A}` are not both present — check both positions when filtering.

## Common uses

- **Guest pitching**: podcasts similar to shows a guest has already appeared on are likely to accept them too.
- **Media list expansion**: start with 5 target shows, expand to 50 via shared-audience hops.
- **Competitive research**: see who overlaps with your own podcast's audience.
- **Recommendation features**: "if you liked X, try Y" in a consumer app.

## Two-hop expansion

Expand beyond direct neighbours by recursing one more level:

```bash
# First hop
FIRST=$(rephonic podcasts similar-graph "$SEED" | jq -r --arg s "$SEED" '.graph.links | map(select(.source == $s or .target == $s)) | sort_by(-.weight) | .[0:5] | .[] | (if .source == $s then .target else .source end)')

# Second hop, dedup against the seed
for pid in $FIRST; do
  rephonic podcasts similar-graph "$pid" | jq -r --arg s "$pid" '.graph.links | map(select(.source == $s or .target == $s)) | sort_by(-.weight) | .[0:3] | .[] | (if .source == $s then .target else .source end)'
done | sort -u
```

## Edge cases

- **Small podcasts may have empty graphs** (insufficient listener data to compute overlap).
- **Seed not found**: Rephonic returns 400, not 404. CLI exits 1. Check stderr for "not found" or "unknown".
- Weights are normalised 0 to 1 within a graph. Don't compare weights across different seed podcasts as absolute values.
