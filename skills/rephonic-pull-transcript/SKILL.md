---
name: rephonic-pull-transcript
description: Fetch the transcript of a podcast episode, with speaker labels and timestamps, and prepare it for LLM prompts, quote extraction, sponsor analysis or keyword search. Use when a user wants to analyze, summarize, search, or quote from a specific podcast episode.
---

# Pull a podcast transcript

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
        "start": 12400,
        "end": 18900,
        "speaker": 1,
        "text": "Today we're joined by Dr. Brian Keating..."
      }
    ],
    "speakers": {
      "1": "Andrew Huberman",
      "2": "Brian Keating"
    }
  },
  "episode": {...}
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

This writes the transcript to a text file with one paragraph per segment, each starting with the speaker's name, which you can paste into an LLM prompt:

```bash
rephonic episodes transcript "$EID" | jq -r '
  .transcript as $t
  | $t.segments
  | map("[" + ($t.speakers[.speaker | tostring] // "Speaker \(.speaker)") + "] " + .text)
  | join("\n\n")
' > transcript.txt
```

## Extract sponsor reads

Sponsor segments commonly cluster in the first few minutes and around the middle of an episode. Filter by timestamp (milliseconds):

```bash
rephonic episodes transcript "$EID" | jq '
  .transcript.segments
  | map(select(.start < 480000 or (.start > 2400000 and .start < 3300000)))
  | map(.text)
  | join(" ")
'
```

For structured sponsor data (ad text, promo codes, URLs), use `rephonic podcasts promotions <podcast_id>` instead. Rephonic has already pulled those out for each podcast.

## Keyword search within a transcript

```bash
rephonic episodes transcript "$EID" | jq '
  .transcript.segments
  | map(select(.text | test("openai"; "i")))
  | map({start, text})
'
```

The `"i"` flag makes the match case-insensitive.

## Edge cases

- Some episodes have no transcript. For those the endpoint returns 400 (`BadRequestError`), not 404, and the CLI exits 1. Look for "not available" or "unknown" in the error on stderr.
- Rephonic doesn't always know who the speakers are, and sometimes it only has numeric speaker IDs. Your code should handle a `speakers` dict that is partial or empty. Its keys are strings (`"1"`), while `segment.speaker` is a number.
- An episode over 2 hours usually has somewhere between 2,000 and 5,000 segments. Use `jq -c` for compact output if you're piping the JSON into another tool.
- Timestamps are integer milliseconds. Divide by 1000 to get seconds, or use Python's `timedelta(milliseconds=start)` if you need HH:MM:SS.
