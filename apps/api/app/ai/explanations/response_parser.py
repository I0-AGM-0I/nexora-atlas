"""
NEXORA ATLAS - Raw AI Response Parser (Phase 9)
Transforms raw LLM text into candidate structured dictionaries/models.

CRITICAL ARCHITECTURAL DISTINCTION:
  Parsing != Validation
  Validation != Evidence

A successfully parsed payload is an UNTRUSTED CANDIDATE.
The downstream AIResponseValidator remains the sole authoritative gate
for mathematical verification, evidence grounding, and epistemic boundary fidelity.
"""

import json
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ParsedCandidateResponse:
    """
    Candidate payload parsed from raw provider output.
    Explicitly marked as UNTRUSTED until passed through deterministic validation gates.
    """
    raw_text: str
    parsed_json: Optional[Dict[str, Any]] = None
    is_syntactically_valid: bool = False
    parse_error: Optional[str] = None


def parse_provider_response(raw_text: str) -> ParsedCandidateResponse:
    """
    Extracts and parses JSON from raw provider output (including Markdown-fenced blocks).
    Does NOT assert or imply validity against Atlas evidence contracts.
    """
    if not raw_text or not raw_text.strip():
        return ParsedCandidateResponse(
            raw_text=raw_text,
            is_syntactically_valid=False,
            parse_error="Empty or whitespace-only response from provider.",
        )

    # Clean Markdown code fencing if present (e.g. ```json ... ```)
    cleaned = raw_text.strip()
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if json_match:
        cleaned = json_match.group(1).strip()

    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            return ParsedCandidateResponse(
                raw_text=raw_text,
                is_syntactically_valid=False,
                parse_error=f"Expected JSON object at root, got {type(parsed).__name__}.",
            )
        return ParsedCandidateResponse(
            raw_text=raw_text,
            parsed_json=parsed,
            is_syntactically_valid=True,
        )
    except json.JSONDecodeError as exc:
        return ParsedCandidateResponse(
            raw_text=raw_text,
            is_syntactically_valid=False,
            parse_error=f"JSON decode failure: {str(exc)}",
        )
