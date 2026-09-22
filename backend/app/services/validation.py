"""Validate untrusted LLM output against schemas and the evidence store.

Architectural decision:
- LLM JSON is untrusted input. extra='forbid' already rejects quote and
  timestamp fields; this layer also checks that every ID exists and was
  in the retrieved set.
- Citing an ID that was not retrieved is treated as unknown. The model
  must not invent provenance from memory of the corpus.
"""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, Field, ValidationError

from app.models.analysis import AnalysisResponse, QAResponse
from app.services.evidence_store import EvidenceStore

TCited = TypeVar("TCited", AnalysisResponse, QAResponse)
TModel = TypeVar("TModel", bound=BaseModel)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class IdValidation(BaseModel):
    valid_ids: list[str]
    unknown_ids: list[str]
    out_of_retrieval_ids: list[str]


class ValidationResult(BaseModel):
    ok: bool
    parsed: AnalysisResponse | QAResponse | None = None
    valid_ids: list[str] = Field(default_factory=list)
    unknown_ids: list[str] = Field(default_factory=list)
    error: str | None = None


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = _FENCE_RE.sub("", text.strip()).strip()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM output is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("LLM output JSON must be an object.")
    return payload


def parse_model(text: str, model: type[TModel]) -> TModel:
    payload = extract_json_object(text)
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"LLM JSON failed schema validation: {exc.error_count()} error(s)") from exc


def parse_cited_answer(text: str, model: type[TCited]) -> TCited:
    return parse_model(text, model)


def classify_evidence_ids(
    evidence_ids: list[str],
    store: EvidenceStore,
    allowed_ids: set[str] | None = None,
) -> IdValidation:
    valid: list[str] = []
    unknown: list[str] = []
    out_of_retrieval: list[str] = []
    seen: set[str] = set()
    for evidence_id in evidence_ids:
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        if store.get(evidence_id) is None:
            unknown.append(evidence_id)
            continue
        if allowed_ids is not None and evidence_id not in allowed_ids:
            out_of_retrieval.append(evidence_id)
            continue
        valid.append(evidence_id)
    return IdValidation(
        valid_ids=valid,
        unknown_ids=unknown,
        out_of_retrieval_ids=out_of_retrieval,
    )


def validate_cited_answer(
    text: str,
    store: EvidenceStore,
    model: type[TCited] = QAResponse,
    allowed_ids: set[str] | None = None,
) -> ValidationResult:
    try:
        parsed = parse_cited_answer(text, model)
    except ValueError as exc:
        return ValidationResult(ok=False, error=str(exc))

    classified = classify_evidence_ids(parsed.evidence_ids, store, allowed_ids)
    invalid = classified.unknown_ids + classified.out_of_retrieval_ids
    if invalid:
        parts: list[str] = []
        if classified.unknown_ids:
            parts.append(f"unknown evidence IDs: {classified.unknown_ids}")
        if classified.out_of_retrieval_ids:
            parts.append(f"IDs not in retrieved set: {classified.out_of_retrieval_ids}")
        return ValidationResult(
            ok=False,
            parsed=parsed,
            valid_ids=classified.valid_ids,
            unknown_ids=invalid,
            error="; ".join(parts),
        )
    return ValidationResult(
        ok=True,
        parsed=parsed,
        valid_ids=classified.valid_ids,
        unknown_ids=[],
    )
