"""Deterministic interview-guide parser.

Architectural decision:
- Guide questions are source data, like transcripts. The parser reads
  Interview_Guide.txt and does not invent questions or rephrase them.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.models.guide import GuideQuestion, InterviewGuide

QUESTION_RE = re.compile(r"^(\d+)\.\s+(.+)$")


class GuideParseError(ValueError):
    """Raised when the interview guide is missing required fields."""


def parse_guide_file(path: str | Path) -> InterviewGuide:
    source = Path(path)
    return parse_guide(source.read_text(encoding="utf-8-sig"), source_path=str(source))


def parse_guide(text: str, *, source_path: str | None = None) -> InterviewGuide:
    del source_path  # reserved for later ingest metadata
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    title = ""
    objective_lines: list[str] = []
    questions: list[GuideQuestion] = []
    in_objective = False

    for raw in lines:
        line = raw.strip()
        if not line:
            if in_objective and objective_lines:
                in_objective = False
            continue

        if not title:
            title = line
            continue

        if line.lower().startswith("project objective:"):
            remainder = line.split(":", 1)[1].strip()
            in_objective = True
            if remainder:
                objective_lines.append(remainder)
            continue

        if line.lower() == "questions:":
            in_objective = False
            continue

        question_match = QUESTION_RE.match(line)
        if question_match:
            in_objective = False
            questions.append(
                GuideQuestion(
                    number=int(question_match.group(1)),
                    text=question_match.group(2).strip(),
                )
            )
            continue

        if in_objective:
            objective_lines.append(line)

    if not title:
        raise GuideParseError("Interview guide is missing a title.")
    objective = " ".join(objective_lines).strip()
    if not objective:
        raise GuideParseError("Interview guide is missing a project objective.")
    if not questions:
        raise GuideParseError("Interview guide has no questions.")
    return InterviewGuide(title=title, objective=objective, questions=questions)
