---
name: rephonic-pull-transcript
description: Fetch a full, timestamped, speaker-labeled transcript of a podcast episode and prepare it for downstream use (LLM pipelines, quote extraction, sponsor analysis, keyword search). Use when a user wants to analyze, summarize, search, or quote from a specific podcast episode.
---

# Pull a podcast transcript

Rephonic ships full transcripts with speaker IDs and timestamps. Use them for LLM pipelines, quote extraction, sponsor analysis, or keyword search within an episode.

## Quick use

```bash
rephonic episodes transcript kzaca-huberman-lab-dr-brian-keating-charting-the-a \
  | jq '.transcript.segments[0:3]'
```

## Response shape

```json
{
  "transcript": {
    "segments": [
      {
        "start": 12.4,
        "end": 18.9,
        "speaker": "S1",
        "text": "Today we're joined by Dr. Brian Keating..."
      }
    ],
    "speakers": {
      "S1": "Andrew Huberman",
      "S2": "Brian Keating"
    }
  }
}
```

## Find the episode ID first

### By search

```bash
rephonic search episodes --query "brian keating huberman" | jq '.episodes[0].id'
```

### By listing a podcast's episodes

```bash
rephonic episodes list --podcast-id huberman-lab --per-page 5 | jq '.episodes[] | {id, title}'
```

## Flatten for LLM input

For prompting an LLM, speaker-prefixed paragraphs are usually cleaner than the raw segment array:

```bash
rephonic episodes transcript "$EID" | jq -r '
  .transcript as $t
  | $t.segments
  | map("[" + ($t.speakers[.speaker] // .speaker) + "] " + .text)
  | join("\n\n")
' > transcript.txt
```

## Extract sponsor reads

Sponsor segments commonly cluster in the first few minutes and around the middle of an episode. Filter by timestamp:

```bash
rephonic episodes transcript "$EID" | jq '
  .transcript.segments
  | map(select(.start < 480 or (.start > 2400 and .start < 3300)))
  | map(.text)
  | join(" ")
'
```

For structured sponsor data (ad text, promo codes, URLs), prefer `rephonic podcasts promotions <podcast_id>` — Rephonic already extracts these at the podcast level.

## Keyword search within a transcript

```bash
rephonic episodes transcript "$EID" | jq '
  .transcript.segments
  | map(select(.text | test("openai"; "i")))
  | map({start, text})
'
```

`"i"` on the regex = case-insensitive.

## Feeding to an LLM

The flattened transcript output is directly usable as Claude or GPT input. For very long episodes (3+ hours, 10k+ segments), chunk by speaker turn and summarize iteratively, or feed via a prompt-caching pipeline.

## Edge cases

- **Not all episodes have transcripts.** The endpoint returns 400 `BadRequestError` (not 404) when missing. CLI exits 1. Check stderr for "not available" or "unknown".
- **Speaker names are best-effort.** Sometimes Rephonic only has speaker IDs (`S1`, `S2`) without named mapping. Handle the `speakers` dict being partial or empty.
- **Long episodes produce big arrays.** Segment arrays in the 2k to 5k range are normal for 2+ hour episodes. Pipe through `jq -c` for compact output if you're streaming to another tool.
- **Timestamps are in seconds (float).** Convert with `date -u -d @"$start"` or Python's `timedelta` if you need HH:MM:SS.
