---
name: pm-transcript-summarizer
description: Summarize timestamped meeting transcripts from source URLs into PM-focused key talking points and big ideas with timestamps for fast playback navigation. Use when a user shares a transcript link and asks for concise synthesis of decisions, priorities, risks, customer insights, metrics, or action items.
---

# PM Transcript Summarizer

Generate timestamped PM-style summaries from transcript text files.

## Workflow

1. Pull transcript data directly from the source URL:

```bash
python3 pm-transcript-summarizer/scripts/pm_transcript_summarizer.py \
  --source-url "https://example.com/transcript-source" \
  --output /absolute/path/summary.md \
  --format markdown \
  --max-points 8 \
  --max-ideas 4
```

2. Supported source URL payloads:
- Plain text transcript files
- JSON payloads (extracts timestamp/text fields when available)
- HTML pages (extracts visible text)
3. Ensure transcript lines include timestamps in one of these formats: `[mm:ss]`, `[hh:mm:ss]`, `mm:ss`, `hh:mm:ss`.
4. Use `--format json` for structured downstream processing.
5. Use `--input /absolute/path/transcript.txt` only when URL access is unavailable.

## Output Contract

- `PM Summary`: one PM-oriented overview paragraph.
- `Key Talking Points`: timestamped bullets with PM category labels.
- `Big Ideas`: recurring PM themes with first-seen timestamps.

## Quality Checks

1. Confirm output file exists and is non-empty.
2. Confirm all three report sections are present.
3. Spot-check at least two timestamps against the source transcript.
