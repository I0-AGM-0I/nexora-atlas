"""
NEXORA ATLAS - Gate 6 & 7: Security & Confidence Prohibition (Phase 9 Milestone 4)
Enforces enterprise security invariants:
- Absolute recursive prohibition of AI-generated confidence scores.
- Detection and rejection of prompt injection execution.
- Prevention of secret / credential leakage (AWS keys, JWTs, DB URLs, tokens).
"""

import re
from typing import List, Dict, Any, Union, Set
from app.ai.providers.models import AICandidateAnswer
from app.ai.validation.result import ValidationViolation
# Secret detection regexes
AWS_ACCESS_KEY_REGEX = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
JWT_REGEX = re.compile(r"\bey[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b")
BEARER_TOKEN_REGEX = re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_=]{20,}")
CONNECTION_STRING_REGEX = re.compile(r"(?i)(postgres|postgresql|mysql|mongodb|redis)://[^:]+:([^@]+)@")


# Prohibited AI-generated confidence score keys
PROHIBITED_CONFIDENCE_KEYS: Set[str] = {
    "confidence",
    "confidence_pct",
    "confidence_score",
    "model_confidence",
    "certainty_score",
}

# Malicious instruction indicators in candidate outputs
MALICIOUS_INSTRUCTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous\s+|prior\s+)?instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(atlas\s+)?rules", re.IGNORECASE),
    re.compile(r"reveal\s+(api\s+keys?|passwords?|credentials?|secrets?)", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*leak", re.IGNORECASE),
    re.compile(r"delete\s+all\s+(data|records|tables|databases)", re.IGNORECASE),
]


class SecurityValidator:
    """
    Gates 6 & 7: Enforces strict confidence score prohibition and security defenses.
    Rejects prompt injections, credential leaks, and prohibited AI confidence values.
    """

    GATE_6_NAME = "GATE_6_CONFIDENCE"
    GATE_7_NAME = "GATE_7_SECURITY"

    @classmethod
    def validate(cls, candidate: Union[AICandidateAnswer, Dict[str, Any]]) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []

        # 1. Gate 6: Recursive check for prohibited confidence keys
        if isinstance(candidate, AICandidateAnswer):
            payload = candidate.raw_json if candidate.raw_json else candidate.model_dump()
        else:
            payload = candidate

        cls._check_no_confidence(payload, "root", violations)

        # 2. Gate 7: Security check for leaked secrets and prompt injection execution
        text_to_scan = cls._extract_text_corpus(candidate)
        cls._check_for_secret_leaks(text_to_scan, violations)
        cls._check_for_injection_execution(text_to_scan, violations)

        return violations

    @classmethod
    def _check_no_confidence(
        cls,
        data: Any,
        path: str,
        violations: List[ValidationViolation],
    ) -> None:
        """Recursively checks for prohibited confidence keys."""
        if isinstance(data, dict):
            for k, v in data.items():
                curr_path = f"{path}.{k}"
                if k.lower() in PROHIBITED_CONFIDENCE_KEYS:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_6_NAME,
                            rule="PROHIBITED_CONFIDENCE_FIELD",
                            message=(
                                f"AI-generated confidence score detected at '{curr_path}'; prohibited by Atlas contract."
                            ),
                            field_path=curr_path,
                        )
                    )
                cls._check_no_confidence(v, curr_path, violations)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                cls._check_no_confidence(item, f"{path}[{idx}]", violations)

    @classmethod
    def _check_for_secret_leaks(
        cls,
        text: str,
        violations: List[ValidationViolation],
    ) -> None:
        """Detects leakage of AWS access keys, JWTs, bearer tokens, or DB URLs."""
        if AWS_ACCESS_KEY_REGEX.search(text):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_7_NAME,
                    rule="SECRET_LEAK_AWS_KEY",
                    message="Security violation: Candidate output contains an unredacted AWS access key.",
                    field_path="text_corpus",
                )
            )

        if JWT_REGEX.search(text):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_7_NAME,
                    rule="SECRET_LEAK_JWT",
                    message="Security violation: Candidate output contains a JWT token.",
                    field_path="text_corpus",
                )
            )

        if BEARER_TOKEN_REGEX.search(text):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_7_NAME,
                    rule="SECRET_LEAK_BEARER_TOKEN",
                    message="Security violation: Candidate output contains an authorization Bearer token.",
                    field_path="text_corpus",
                )
            )

        if CONNECTION_STRING_REGEX.search(text):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_7_NAME,
                    rule="SECRET_LEAK_DATABASE_URL",
                    message="Security violation: Candidate output contains a database connection string.",
                    field_path="text_corpus",
                )
            )

    @classmethod
    def _check_for_injection_execution(
        cls,
        text: str,
        violations: List[ValidationViolation],
    ) -> None:
        """Detects candidate following hostile prompt injection instructions."""
        for pattern in MALICIOUS_INSTRUCTION_PATTERNS:
            if pattern.search(text):
                violations.append(
                    ValidationViolation(
                        gate=cls.GATE_7_NAME,
                        rule="PROMPT_INJECTION_FOLLOWED",
                        message=(
                            "Security violation: Candidate output exhibits compliance with hostile prompt injection."
                        ),
                        field_path="text_corpus",
                    )
                )
                break

    @classmethod
    def _extract_text_corpus(cls, candidate: Union[AICandidateAnswer, Dict[str, Any]]) -> str:
        """Extracts all text fields from candidate for scanning."""
        if isinstance(candidate, AICandidateAnswer):
            parts = [candidate.summary, candidate.answer]
            for c in candidate.conclusions:
                parts.append(c.statement)
            parts.extend(candidate.limitations)
            parts.extend(candidate.recommended_next_steps)
            parts.extend(candidate.epistemic_notes)
            return " ".join(parts)
        elif isinstance(candidate, dict):
            import json
            return json.dumps(candidate)
        return ""
