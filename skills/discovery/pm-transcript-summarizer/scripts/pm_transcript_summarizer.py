#!/usr/bin/env python3
"""PM-focused transcript summarizer with timestamped talking points and themes."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import URLError
from urllib.request import Request, urlopen

TIMESTAMP_RE = re.compile(
    r"^\s*(?:\[(?P<bracketed>\d{1,2}:\d{2}(?::\d{2})?)\]|(?P<plain>\d{1,2}:\d{2}(?::\d{2})?))\s*(?:-|–|—)?\s*(?:(?P<speaker>[^:]{1,40}):\s*)?(?P<text>.*\S)?\s*$"
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
WORD_RE = re.compile(r"[a-zA-Z0-9']+")
HTML_TAG_RE = re.compile(r"<[a-zA-Z!/]")
TIMESTAMP_VALUE_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")
SECONDS_VALUE_RE = re.compile(r"^\d+(?:\.\d+)?s?$")

JSON_TEXT_KEYS = ("transcript", "text", "content", "body", "caption", "utterance", "line")
JSON_TIME_KEYS = ("timestamp", "time", "start", "start_time", "offset")
JSON_SPEAKER_KEYS = ("speaker", "author", "name", "participant")

FILLER_WORDS = {
    "um",
    "uh",
    "like",
    "you",
    "know",
    "basically",
    "actually",
    "literally",
    "sort",
    "kind",
    "just",
    "maybe",
    "probably",
    "really",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "there",
    "this",
    "to",
    "we",
    "with",
}

CATEGORY_RULES: Dict[str, Dict[str, object]] = {
    "customer_problem": {
        "label": "Customer Problem",
        "weight": 3,
        "keywords": {
            "customer",
            "user",
            "pain",
            "problem",
            "friction",
            "complaint",
            "confusion",
            "dropoff",
            "churn",
            "support",
            "ticket",
            "feedback",
        },
    },
    "strategy": {
        "label": "Product Strategy",
        "weight": 3,
        "keywords": {
            "vision",
            "strategy",
            "positioning",
            "market",
            "segment",
            "differentiation",
            "value",
            "north",
            "star",
            "bet",
            "focus",
        },
    },
    "prioritization": {
        "label": "Prioritization",
        "weight": 3,
        "keywords": {
            "priority",
            "prioritize",
            "tradeoff",
            "scope",
            "roadmap",
            "sprint",
            "backlog",
            "sequence",
            "phase",
            "must",
            "should",
            "later",
            "first",
        },
    },
    "execution": {
        "label": "Execution Plan",
        "weight": 2,
        "keywords": {
            "build",
            "implement",
            "ship",
            "release",
            "launch",
            "timeline",
            "owner",
            "deadline",
            "deliver",
            "next",
            "action",
            "followup",
        },
    },
    "risk": {
        "label": "Risks & Dependencies",
        "weight": 3,
        "keywords": {
            "risk",
            "dependency",
            "blocker",
            "concern",
            "assumption",
            "legal",
            "security",
            "compliance",
            "integration",
            "delay",
        },
    },
    "metric": {
        "label": "Metrics & Outcomes",
        "weight": 4,
        "keywords": {
            "metric",
            "kpi",
            "goal",
            "target",
            "conversion",
            "retention",
            "adoption",
            "revenue",
            "cost",
            "impact",
            "success",
            "baseline",
            "measure",
            "experiment",
            "percent",
        },
    },
}

TAG_PRIORITY = [
    "metric",
    "customer_problem",
    "risk",
    "prioritization",
    "execution",
    "strategy",
]


@dataclass
class TranscriptEntry:
    timestamp_seconds: int
    timestamp: str
    speaker: Optional[str]
    text: str
    cleaned_text: str = ""
    tokens: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    score: float = 0.0


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []
        self._skip_stack: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._skip_stack:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def get_text(self) -> str:
        return "\n".join(self._chunks)


def _looks_like_json(text: str) -> bool:
    stripped = text.lstrip()
    return bool(stripped) and stripped[0] in {"{", "["}


def _looks_like_html(text: str) -> bool:
    preview = text[:500]
    return bool(HTML_TAG_RE.search(preview))


def _parse_timestamp_value(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return format_timestamp(int(value))

    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        if TIMESTAMP_VALUE_RE.match(candidate):
            return format_timestamp(parse_timestamp(candidate))
        if SECONDS_VALUE_RE.match(candidate):
            cleaned = candidate[:-1] if candidate.endswith("s") else candidate
            return format_timestamp(int(float(cleaned)))

    return None


def _extract_text_from_html(html_text: str) -> List[str]:
    parser = _HTMLTextExtractor()
    parser.feed(html_text)
    parser.close()
    content = unescape(parser.get_text())
    return content.splitlines()


def _stringify_json(node: object) -> str:
    parts: List[str] = []

    def walk(value: object) -> None:
        if isinstance(value, str):
            text = value.strip()
            if text:
                parts.append(text)
            return
        if isinstance(value, dict):
            for sub in value.values():
                walk(sub)
            return
        if isinstance(value, list):
            for sub in value:
                walk(sub)

    walk(node)
    return "\n".join(parts)


def _extract_lines_from_json(node: object) -> List[str]:
    extracted: List[str] = []

    def walk(value: object) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return

        if not isinstance(value, dict):
            return

        raw_text: Optional[str] = None
        for key in JSON_TEXT_KEYS:
            maybe = value.get(key)
            if isinstance(maybe, str) and maybe.strip():
                raw_text = maybe.strip()
                break

        timestamp: Optional[str] = None
        for key in JSON_TIME_KEYS:
            timestamp = _parse_timestamp_value(value.get(key))
            if timestamp:
                break

        speaker: Optional[str] = None
        for key in JSON_SPEAKER_KEYS:
            maybe_speaker = value.get(key)
            if isinstance(maybe_speaker, str) and maybe_speaker.strip():
                speaker = maybe_speaker.strip()
                break

        if raw_text and timestamp:
            prefix = f"{speaker}: " if speaker else ""
            extracted.append(f"[{timestamp}] {prefix}{raw_text}")

        for sub in value.values():
            walk(sub)

    walk(node)

    if extracted:
        return extracted

    raw = _stringify_json(node)
    return raw.splitlines()


def load_transcript_lines(input_path: Optional[str], source_url: Optional[str]) -> List[str]:
    if source_url:
        request = Request(source_url, headers={"User-Agent": "pm-transcript-summarizer/1.0"})
        try:
            with urlopen(request, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                encoding = response.headers.get_content_charset() or "utf-8"
                body = response.read().decode(encoding, errors="replace")
        except URLError as exc:
            raise SystemExit(f"Unable to fetch source URL: {exc}") from exc

        if "json" in content_type or _looks_like_json(body):
            try:
                payload = json.loads(body)
                return _extract_lines_from_json(payload)
            except json.JSONDecodeError:
                pass

        if "html" in content_type or _looks_like_html(body):
            return _extract_text_from_html(body)

        return body.splitlines()

    if input_path:
        with open(input_path, "r", encoding="utf-8") as f:
            return f.readlines()

    raise SystemExit("Provide either --input or --source-url")


def parse_timestamp(value: str) -> int:
    parts = [int(p) for p in value.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"Unsupported timestamp: {value}")


def format_timestamp(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def simple_stem(token: str) -> str:
    if token.endswith("'s"):
        token = token[:-2]
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)]
    return token


def clean_text(text: str) -> str:
    tokens = tokenize(text)
    kept = [tok for tok in tokens if tok not in FILLER_WORDS]
    return " ".join(kept).strip()


def parse_transcript(lines: Iterable[str]) -> List[TranscriptEntry]:
    entries: List[TranscriptEntry] = []

    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue

        match = TIMESTAMP_RE.match(line)
        if match:
            raw_ts = match.group("bracketed") or match.group("plain")
            text = (match.group("text") or "").strip()
            if not text:
                continue

            seconds = parse_timestamp(raw_ts)
            speaker = match.group("speaker")
            entry = TranscriptEntry(
                timestamp_seconds=seconds,
                timestamp=format_timestamp(seconds),
                speaker=speaker.strip() if speaker else None,
                text=text,
            )
            entries.append(entry)
            continue

        if entries:
            entries[-1].text = f"{entries[-1].text} {line.strip()}".strip()

    return entries


def classify_categories(tokens: Sequence[str]) -> List[str]:
    token_set = set(tokens)
    stemmed_set = {simple_stem(t) for t in token_set}
    search_set = token_set.union(stemmed_set)
    matched: List[str] = []
    for category, config in CATEGORY_RULES.items():
        keywords = config["keywords"]
        if search_set.intersection(keywords):
            matched.append(category)
    return matched


def lexical_score(tokens: Sequence[str], frequencies: Dict[str, int]) -> float:
    score = 0.0
    unique_tokens = set(tokens)
    for token in unique_tokens:
        if token in STOPWORDS or len(token) <= 2:
            continue
        freq = frequencies.get(token, 1)
        score += 1.0 / freq
    return score


def action_signal(text: str) -> float:
    lower = text.lower()
    score = 0.0
    if re.search(r"\b(should|need to|let's|next step|action item|owner|by\s+\w+)\b", lower):
        score += 2.5
    if re.search(r"\b(decide|decision|agreed|commit|plan)\b", lower):
        score += 1.5
    if re.search(r"\d", lower):
        score += 1.0
    return score


def select_primary_tag(categories: Sequence[str]) -> str:
    for tag in TAG_PRIORITY:
        if tag in categories:
            return tag
    return "strategy"


def summarize_sentence(text: str, max_words: int = 26) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ""
    sentence = SENTENCE_SPLIT_RE.split(cleaned)[0]
    words = sentence.split()
    if len(words) <= max_words:
        return sentence.rstrip(".")
    return " ".join(words[:max_words]).rstrip(".,") + "..."


def analyze_entries(entries: List[TranscriptEntry]) -> List[TranscriptEntry]:
    all_tokens: List[str] = []
    for entry in entries:
        entry.cleaned_text = clean_text(entry.text)
        entry.tokens = tokenize(entry.cleaned_text)
        all_tokens.extend(entry.tokens)

    frequencies: Dict[str, int] = {}
    for token in all_tokens:
        frequencies[token] = frequencies.get(token, 0) + 1

    for entry in entries:
        if not entry.tokens:
            entry.score = 0.0
            continue

        entry.categories = classify_categories(entry.tokens)
        base = lexical_score(entry.tokens, frequencies)
        category_bonus = sum(CATEGORY_RULES[c]["weight"] for c in entry.categories)
        signal_bonus = action_signal(entry.cleaned_text)
        length_bonus = min(len(entry.tokens) / 20.0, 1.0)

        entry.score = base + float(category_bonus) + signal_bonus + length_bonus

    return entries


def is_low_signal(entry: TranscriptEntry) -> bool:
    if len(entry.tokens) < 4:
        return True
    meaningful = [t for t in entry.tokens if t not in STOPWORDS and len(t) > 2]
    return len(meaningful) < 3


def choose_key_points(
    entries: List[TranscriptEntry],
    max_points: int,
    min_gap_seconds: int = 75,
) -> List[TranscriptEntry]:
    candidates = [e for e in entries if not is_low_signal(e) and e.score > 0]
    ordered = sorted(candidates, key=lambda e: e.score, reverse=True)

    chosen: List[TranscriptEntry] = []
    for entry in ordered:
        if len(chosen) >= max_points:
            break
        if any(abs(entry.timestamp_seconds - c.timestamp_seconds) < min_gap_seconds for c in chosen):
            continue
        chosen.append(entry)

    # Backfill without gap filtering so short transcripts still return enough highlights.
    if len(chosen) < max_points:
        chosen_ids = {id(e) for e in chosen}
        for entry in ordered:
            if len(chosen) >= max_points:
                break
            if id(entry) in chosen_ids:
                continue
            chosen.append(entry)
            chosen_ids.add(id(entry))

    return sorted(chosen, key=lambda e: e.timestamp_seconds)


def derive_big_ideas(entries: List[TranscriptEntry], max_ideas: int) -> List[Tuple[str, int, str]]:
    buckets: Dict[str, List[TranscriptEntry]] = {k: [] for k in CATEGORY_RULES}
    for entry in entries:
        for category in entry.categories:
            buckets[category].append(entry)

    scored: List[Tuple[str, float]] = []
    for category, bucket_entries in buckets.items():
        if not bucket_entries:
            continue
        total = sum(e.score for e in bucket_entries)
        breadth = len(bucket_entries) * 0.8
        scored.append((category, total + breadth))

    scored.sort(key=lambda item: item[1], reverse=True)

    ideas: List[Tuple[str, int, str]] = []
    used_signatures: set = set()
    for category, _ in scored[:max_ideas]:
        bucket_entries = sorted(buckets[category], key=lambda e: e.timestamp_seconds)
        first_ts = bucket_entries[0].timestamp_seconds
        label = CATEGORY_RULES[category]["label"]

        strongest = max(bucket_entries, key=lambda e: e.score)
        synthesis = summarize_sentence(strongest.text)
        if not synthesis:
            continue
        signature = synthesis.lower()
        if signature in used_signatures:
            continue
        used_signatures.add(signature)

        sentence = f"{label}: {synthesis}."
        ideas.append((label, first_ts, sentence))

    return ideas


def build_pm_summary(key_points: List[TranscriptEntry], big_ideas: List[Tuple[str, int, str]]) -> str:
    if not key_points and not big_ideas:
        return "Transcript did not include enough high-signal PM content to summarize."

    focus_tags = [select_primary_tag(k.categories) for k in key_points]
    counts: Dict[str, int] = {}
    for tag in focus_tags:
        counts[tag] = counts.get(tag, 0) + 1

    ordered_tags = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_labels = [CATEGORY_RULES[tag]["label"] for tag, _ in ordered_tags[:3]]

    if not top_labels:
        top_labels = ["Product Strategy"]

    return (
        "This conversation concentrates on "
        + ", ".join(top_labels)
        + ", with specific moments called out below so a PM can quickly revisit decisions, risks, and outcome signals."
    )


def build_report(entries: List[TranscriptEntry], max_points: int, max_ideas: int) -> Dict[str, object]:
    analyzed = analyze_entries(entries)
    key_points = choose_key_points(analyzed, max_points=max_points)
    big_ideas = derive_big_ideas(analyzed, max_ideas=max_ideas)
    pm_summary = build_pm_summary(key_points, big_ideas)

    key_payload = []
    for point in key_points:
        category_label = CATEGORY_RULES[select_primary_tag(point.categories)]["label"]
        summary = summarize_sentence(point.text)
        key_payload.append(
            {
                "timestamp": point.timestamp,
                "speaker": point.speaker,
                "category": category_label,
                "summary": summary,
            }
        )

    ideas_payload = []
    for label, ts_seconds, text in big_ideas:
        ideas_payload.append(
            {
                "first_timestamp": format_timestamp(ts_seconds),
                "theme": label,
                "summary": text,
            }
        )

    return {
        "pm_summary": pm_summary,
        "key_talking_points": key_payload,
        "big_ideas": ideas_payload,
    }


def to_markdown(report: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# PM Transcript Summary")
    lines.append("")
    lines.append("## PM Summary")
    lines.append(report["pm_summary"])
    lines.append("")
    lines.append("## Key Talking Points")

    points = report.get("key_talking_points", [])
    if not points:
        lines.append("- No high-signal talking points detected.")
    else:
        for item in points:
            speaker = f" ({item['speaker']})" if item.get("speaker") else ""
            lines.append(
                f"- **{item['timestamp']}**{speaker} [{item['category']}]: {item['summary']}"
            )

    lines.append("")
    lines.append("## Big Ideas")

    ideas = report.get("big_ideas", [])
    if not ideas:
        lines.append("- No recurring PM themes detected.")
    else:
        for item in ideas:
            lines.append(
                f"- **{item['first_timestamp']}** [{item['theme']}]: {item['summary']}"
            )

    lines.append("")
    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PM-focused transcript summarizer")
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input", help="Path to timestamped transcript text file")
    source_group.add_argument(
        "--source-url",
        help="Source URL containing transcript data (text, JSON, or HTML)",
    )
    parser.add_argument("--output", required=True, help="Path to write summary report")
    parser.add_argument(
        "--max-points",
        type=int,
        default=8,
        help="Maximum number of key talking points to include",
    )
    parser.add_argument(
        "--max-ideas",
        type=int,
        default=4,
        help="Maximum number of big ideas/themes to include",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    return parser.parse_args(argv)


def run(
    output_path: str,
    max_points: int,
    max_ideas: int,
    output_format: str,
    input_path: Optional[str] = None,
    source_url: Optional[str] = None,
) -> None:
    lines = load_transcript_lines(input_path=input_path, source_url=source_url)
    entries = parse_transcript(lines)
    report = build_report(entries, max_points=max_points, max_ideas=max_ideas)

    if output_format == "json":
        out = json.dumps(report, indent=2)
    else:
        out = to_markdown(report)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(out)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    if args.max_points <= 0:
        raise SystemExit("--max-points must be greater than 0")
    if args.max_ideas <= 0:
        raise SystemExit("--max-ideas must be greater than 0")

    run(
        output_path=args.output,
        max_points=args.max_points,
        max_ideas=args.max_ideas,
        output_format=args.format,
        input_path=args.input,
        source_url=args.source_url,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
