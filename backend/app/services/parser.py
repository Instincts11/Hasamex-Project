"""Deterministic transcript parser.

Architectural decision:
- Parsing is code, not an LLM. Quotes, timestamps, speakers, and header
  metadata must come from the file or be absent.
- A missing MM:SS line becomes timestamp=None. Neighboring times are
  never used to invent a stamp.
- Speaker text is untrusted data. The parser stores it as a string and
  never treats a turn as instructions.
- Only trailing whitespace is stripped. Wording is otherwise unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.models.transcript import Transcript, TranscriptSegment

EXPERT_HEADER = re.compile(r"^Expert\s+\d+\s+[–—-]\s+(.+)$")
ROLE_HEADER = re.compile(r"^Role:\s*(.+)$", re.IGNORECASE)
MARKET_HEADER = re.compile(r"^Market:\s*(.+)$", re.IGNORECASE)
TIMESTAMP_LINE = re.compile(r"^\d{2}:\d{2}$")
SPEAKER_LINE = re.compile(r"^([^:]+):\s*(.*)$")


class TranscriptParseError(ValueError):
    """Raised when a transcript file is missing required header fields."""


def market_to_transcript_id(market: str) -> str:
    """Stable slug used as transcript_id. Derived only from header market."""
    slug = re.sub(r"[^a-z0-9]+", "_", market.strip().lower()).strip("_")
    if not slug:
        raise TranscriptParseError("Market header produced an empty transcript_id.")
    return slug


def parse_transcript_file(path: str | Path) -> Transcript:
    source = Path(path)
    text = source.read_text(encoding="utf-8-sig")
    return parse_transcript(text, source_path=str(source))


def parse_transcript(text: str, *, source_path: str | None = None) -> Transcript:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    expert, role, market, body_start = _parse_header(lines)
    transcript_id = market_to_transcript_id(market)
    segments = _parse_turns(
        lines[body_start:],
        transcript_id=transcript_id,
        expert=expert,
        role=role,
        market=market,
    )
    return Transcript(
        transcript_id=transcript_id,
        expert=expert,
        role=role,
        market=market,
        source_path=source_path,
        segments=segments,
    )


def _parse_header(lines: list[str]) -> tuple[str, str, str, int]:
    expert: str | None = None
    role: str | None = None
    market: str | None = None
    body_start = 0

    for index, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            if expert and role and market:
                body_start = index + 1
                break
            continue

        expert_match = EXPERT_HEADER.match(line)
        if expert_match and expert is None:
            expert = expert_match.group(1).strip()
            continue

        role_match = ROLE_HEADER.match(line)
        if role_match and role is None:
            role = role_match.group(1).strip()
            continue

        market_match = MARKET_HEADER.match(line)
        if market_match and market is None:
            market = market_match.group(1).strip()
            continue

        # First non-header content starts the body. Do not skip it.
        body_start = index
        break
    else:
        body_start = len(lines)

    missing = [
        name
        for name, value in (("expert", expert), ("role", role), ("market", market))
        if not value
    ]
    if missing:
        raise TranscriptParseError(
            f"Transcript header is missing required field(s): {', '.join(missing)}."
        )

    return expert, role, market, body_start


def _parse_turns(
    lines: list[str],
    *,
    transcript_id: str,
    expert: str,
    role: str,
    market: str,
) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    pending_timestamp: str | None = None
    speaker: str | None = None
    timestamp: str | None = None
    text_parts: list[str] = []

    def flush() -> None:
        nonlocal speaker, timestamp, text_parts
        if speaker is None:
            text_parts = []
            timestamp = None
            return
        text = _join_text(text_parts)
        if text:
            segments.append(
                TranscriptSegment(
                    segment_id=_segment_id(transcript_id, len(segments) + 1),
                    transcript_id=transcript_id,
                    expert=expert,
                    role=role,
                    market=market,
                    speaker=speaker,
                    timestamp=timestamp,
                    text=text,
                )
            )
        speaker = None
        timestamp = None
        text_parts = []

    for raw in lines:
        line = raw.rstrip()
        if TIMESTAMP_LINE.match(line):
            flush()
            pending_timestamp = line
            continue

        speaker_match = SPEAKER_LINE.match(line)
        if speaker_match:
            flush()
            speaker = speaker_match.group(1).strip()
            timestamp = pending_timestamp
            pending_timestamp = None
            opening_text = speaker_match.group(2).rstrip()
            text_parts = [opening_text] if opening_text else []
            continue

        if not line:
            continue

        if speaker is None:
            # Text without a speaker is dropped rather than inventing one.
            pending_timestamp = None
            continue

        text_parts.append(line)

    flush()
    return segments


def _join_text(parts: list[str]) -> str:
    return "\n".join(part for part in parts if part).strip()


def _segment_id(transcript_id: str, index: int) -> str:
    return f"seg_{transcript_id}_{index:03d}"
