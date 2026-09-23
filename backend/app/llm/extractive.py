"""Key-free provider that only cites IDs present in the prompt.

Architectural decision:
- The API must run without an OpenAI key for local demo and tests.
- This provider never invents evidence IDs, quotes, or timestamps. It
  only repeats IDs and wording already in the prompt's evidence blocks.
- Unsupported price-style questions return the canonical no-evidence
  answer when no price figure exists in the retrieved text.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.llm.client import ChatMessage, LLMRawCompletion
from app.models.analysis import NO_EVIDENCE_ANSWER

EVIDENCE_BLOCK_RE = re.compile(
    r'<evidence id="(?P<id>[^"]+)">\s*'
    r"expert: (?P<expert>[^\n]+)\s*"
    r"role: (?P<role>[^\n]+)\s*"
    r"market: (?P<market>[^\n]+)\s*"
    r"timestamp: (?P<timestamp>[^\n]+)\s*"
    r"text: (?P<text>.*?)\s*</evidence>",
    re.DOTALL,
)

PRICE_QUESTION_RE = re.compile(r"\b(price|priced|usd|eur|dollar|euro)\b", re.IGNORECASE)
PRICE_EVIDENCE_RE = re.compile(r"€|\$|\bprice\b|\busd\b|\beur\b|\baverage\b", re.IGNORECASE)

THEME_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Purchase timelines", re.compile(r"\b(month|timeline|cycle)\b", re.I)),
    ("Economic constraints", re.compile(r"cost|budget|capital|roi|economic|finance|funding", re.I)),
    ("Training and utilisation", re.compile(r"train|surgeon|utilis", re.I)),
    ("Clinical strategy", re.compile(r"clinical|outcome|strategy", re.I)),
    ("Adoption and growth", re.compile(r"adopt|growth|percent|digit|procedur", re.I)),
)


@dataclass(frozen=True)
class _Block:
    evidence_id: str
    expert: str
    role: str
    market: str
    text: str


class ExtractiveLLMProvider:
    """Deterministic stand-in used when no LLM API key is configured."""

    def __init__(self) -> None:
        self.model_name = "extractive-local"

    def complete(self, messages: list[ChatMessage]) -> LLMRawCompletion:
        combined = "\n".join(item.content for item in messages)
        blocks = _parse_blocks(combined)
        if "Extract scoped claims" in combined:
            payload = _claims_payload(blocks)
        elif "Group into themes" in combined:
            payload = _themes_payload(blocks)
        else:
            payload = _answer_payload(_question_from_messages(messages), blocks)
        return LLMRawCompletion(
            content=json.dumps(payload),
            model=self.model_name,
            latency_ms=0.0,
            prompt_tokens=0,
            completion_tokens=0,
        )


def _parse_blocks(text: str) -> list[_Block]:
    blocks: list[_Block] = []
    seen: set[str] = set()
    for match in EVIDENCE_BLOCK_RE.finditer(text):
        evidence_id = match.group("id")
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        blocks.append(
            _Block(
                evidence_id=evidence_id,
                expert=match.group("expert").strip(),
                role=match.group("role").strip(),
                market=match.group("market").strip(),
                text=match.group("text").strip(),
            )
        )
    return blocks


def _question_from_messages(messages: list[ChatMessage]) -> str:
    content = messages[-1].content if messages else ""
    for prefix in ("User question:", "Interview-guide question:"):
        if prefix in content:
            remainder = content.split(prefix, 1)[1]
            return remainder.split("\n", 1)[0].strip()
    return ""


def _answer_payload(question: str, blocks: list[_Block]) -> dict[str, object]:
    if _is_unsupported_price_question(question, blocks) or not blocks:
        return {"answer": NO_EVIDENCE_ANSWER, "evidence_ids": []}
    selected = _first_block_per_market(blocks)
    parts = [f"{block.market}: {block.text.split('.')[0].strip()}." for block in selected]
    return {
        "answer": " ".join(parts),
        "evidence_ids": [block.evidence_id for block in selected],
    }


def _first_block_per_market(blocks: list[_Block]) -> list[_Block]:
    """Keep the first block from each market.

    Architectural decision:
    - Retrieval already ranked the prompt blocks. Dumping every neighbor
      makes the demo unfocused and tanks citation precision.
    - The first France / Germany / UK block is the top hit for that
      market. Later duplicates are dropped, not rewritten.
    """
    selected: list[_Block] = []
    seen: set[str] = set()
    for block in blocks:
        if block.market in seen:
            continue
        seen.add(block.market)
        selected.append(block)
    return selected


def _is_unsupported_price_question(question: str, blocks: list[_Block]) -> bool:
    if not PRICE_QUESTION_RE.search(question):
        return False
    return not any(PRICE_EVIDENCE_RE.search(block.text) for block in blocks)


def _claims_payload(blocks: list[_Block]) -> dict[str, object]:
    claims = []
    for block in blocks:
        topic = _topic_for(block.text)
        claims.append(
            {
                "topic": topic,
                "claim": block.text.split(".")[0].strip() + ".",
                "scope": block.market,
                "evidence_ids": [block.evidence_id],
            }
        )
    return {"claims": claims}


def _themes_payload(blocks: list[_Block]) -> dict[str, object]:
    grouped: dict[str, list[_Block]] = {}
    for block in blocks:
        grouped.setdefault(_topic_for(block.text), []).append(block)

    themes = []
    for name, items in grouped.items():
        supporting = [item.evidence_id for item in items]
        conflicting = [
            item.evidence_id
            for item in items
            if "balanced" in item.text.lower() and name == "Economic constraints"
        ]
        supporting = [item_id for item_id in supporting if item_id not in conflicting]
        if not supporting and not conflicting:
            continue
        themes.append(
            {
                "name": name,
                "summary": _theme_summary(name, items),
                "supporting_evidence_ids": supporting,
                "conflicting_evidence_ids": conflicting,
            }
        )

    differences = []
    growth = grouped.get("Adoption and growth", [])
    if len({item.market for item in growth}) >= 2:
        differences.append(
            {
                "topic": "Growth rate and scope",
                "summary": "Growth expectations share a topic but differ by market scope.",
                "evidence_ids": [item.evidence_id for item in growth],
            }
        )
    economics = grouped.get("Economic constraints", [])
    if len({item.market for item in economics}) >= 2:
        differences.append(
            {
                "topic": "Role of economics in purchasing",
                "summary": "Experts discuss economics, with different weight on clinical strategy.",
                "evidence_ids": [item.evidence_id for item in economics],
            }
        )
    timelines = grouped.get("Purchase timelines", [])
    if len({item.market for item in timelines}) >= 2:
        differences.append(
            {
                "topic": "Purchase timelines",
                "summary": "Reported decision timelines differ by market and funding condition.",
                "evidence_ids": [item.evidence_id for item in timelines],
            }
        )
    return {"themes": themes, "differences": differences}


def _topic_for(text: str) -> str:
    for name, pattern in THEME_RULES:
        if pattern.search(text):
            return name
    return "Other observations"


def _theme_summary(name: str, items: list[_Block]) -> str:
    markets = sorted({item.market for item in items})
    if len(markets) == 1:
        return f"{name} is discussed by the {markets[0]} expert."
    return f"{name} appears across {', '.join(markets)}."
