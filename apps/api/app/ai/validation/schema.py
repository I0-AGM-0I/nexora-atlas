"""
NEXORA ATLAS - Gate 1: Schema Validation (Phase 9 Milestone 4)
Performs deterministic structural validation on untrusted AI candidate answers.
Guarantees required fields, types, Decimal coercion, and enum compliance.
"""

from typing import List, Dict, Any, Union
from decimal import Decimal, InvalidOperation

from app.ai.types import EpistemicClass
from app.ai.providers.models import AICandidateAnswer, AICandidateConclusion, AICandidateNumericClaim
from app.ai.validation.result import ValidationViolation


class SchemaValidator:
    """
    Gate 1: Verifies that candidate output matches the required schema.
    A candidate failing schema validation never reaches subsequent semantic gates.
    """

    GATE_NAME = "GATE_1_SCHEMA"

    @classmethod
    def validate(cls, candidate: Union[AICandidateAnswer, Dict[str, Any]]) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []

        if isinstance(candidate, AICandidateAnswer):
            return cls._validate_candidate_object(candidate)
        elif isinstance(candidate, dict):
            return cls._validate_candidate_dict(candidate)
        else:
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="VALID_CANDIDATE_PAYLOAD",
                    message=f"Candidate payload must be AICandidateAnswer or dict, got {type(candidate).__name__}.",
                    field_path="root",
                )
            )
            return violations

    @classmethod
    def _validate_candidate_object(cls, candidate: AICandidateAnswer) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []

        if not candidate.summary or not candidate.summary.strip():
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="REQUIRED_SUMMARY",
                    message="Candidate summary must be a non-empty string.",
                    field_path="summary",
                )
            )

        if not candidate.answer or not candidate.answer.strip():
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="REQUIRED_ANSWER",
                    message="Candidate answer must be a non-empty string.",
                    field_path="answer",
                )
            )

        if not isinstance(candidate.conclusions, list):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="CONCLUSIONS_LIST",
                    message="Candidate conclusions must be a list.",
                    field_path="conclusions",
                )
            )
        else:
            for idx, concl in enumerate(candidate.conclusions):
                cls._validate_conclusion(concl, idx, violations)

        if not isinstance(candidate.limitations, list):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="LIMITATIONS_LIST",
                    message="Candidate limitations must be a list of strings.",
                    field_path="limitations",
                )
            )

        if not isinstance(candidate.recommended_next_steps, list):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="RECOMMENDED_STEPS_LIST",
                    message="Candidate recommended_next_steps must be a list of strings.",
                    field_path="recommended_next_steps",
                )
            )

        return violations

    @classmethod
    def _validate_conclusion(
        cls,
        concl: AICandidateConclusion,
        idx: int,
        violations: List[ValidationViolation],
    ) -> None:
        path = f"conclusions[{idx}]"
        if not concl.statement or not concl.statement.strip():
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="CONCLUSION_STATEMENT_REQUIRED",
                    message=f"Conclusion at index {idx} has an empty statement.",
                    field_path=f"{path}.statement",
                )
            )

        if not isinstance(concl.epistemic_class, EpistemicClass):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="INVALID_EPISTEMIC_CLASS_ENUM",
                    message=f"Conclusion at index {idx} has invalid epistemic_class '{concl.epistemic_class}'.",
                    field_path=f"{path}.epistemic_class",
                )
            )

        if not isinstance(concl.evidence_ids, list):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="EVIDENCE_IDS_LIST",
                    message=f"Conclusion at index {idx} evidence_ids must be a list.",
                    field_path=f"{path}.evidence_ids",
                )
            )

        if not isinstance(concl.numeric_claims, list):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="NUMERIC_CLAIMS_LIST",
                    message=f"Conclusion at index {idx} numeric_claims must be a list.",
                    field_path=f"{path}.numeric_claims",
                )
            )
        else:
            for c_idx, claim in enumerate(concl.numeric_claims):
                c_path = f"{path}.numeric_claims[{c_idx}]"
                if not isinstance(claim.value, Decimal):
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="NUMERIC_CLAIM_DECIMAL_REQUIRED",
                            message=f"Numeric claim at {c_path} value must be a Decimal, got {type(claim.value).__name__}.",
                            field_path=f"{c_path}.value",
                        )
                    )
                if not claim.unit or not str(claim.unit).strip():
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="NUMERIC_CLAIM_UNIT_REQUIRED",
                            message=f"Numeric claim at {c_path} must specify a unit.",
                            field_path=f"{c_path}.unit",
                        )
                    )

    @classmethod
    def _validate_candidate_dict(cls, data: Dict[str, Any]) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []
        for req_field in ("summary", "answer"):
            val = data.get(req_field)
            if not val or not isinstance(val, str) or not val.strip():
                violations.append(
                    ValidationViolation(
                        gate=cls.GATE_NAME,
                        rule=f"REQUIRED_{req_field.upper()}",
                        message=f"Candidate field '{req_field}' must be a non-empty string.",
                        field_path=req_field,
                    )
                )

        conclusions = data.get("conclusions")
        if conclusions is None or not isinstance(conclusions, list):
            violations.append(
                ValidationViolation(
                    gate=cls.GATE_NAME,
                    rule="CONCLUSIONS_LIST",
                    message="Candidate 'conclusions' must be a list.",
                    field_path="conclusions",
                )
            )
        else:
            for idx, c in enumerate(conclusions):
                if not isinstance(c, dict):
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="CONCLUSION_DICT",
                            message=f"Conclusion at index {idx} must be a dictionary.",
                            field_path=f"conclusions[{idx}]",
                        )
                    )
                    continue

                if not c.get("statement") or not str(c.get("statement", "")).strip():
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="CONCLUSION_STATEMENT_REQUIRED",
                            message=f"Conclusion at index {idx} has an empty statement.",
                            field_path=f"conclusions[{idx}].statement",
                        )
                    )

                ep_raw = str(c.get("epistemic_class", "")).upper()
                try:
                    EpistemicClass(ep_raw)
                except ValueError:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="INVALID_EPISTEMIC_CLASS_ENUM",
                            message=f"Conclusion at index {idx} has unrecognized epistemic_class '{ep_raw}'.",
                            field_path=f"conclusions[{idx}].epistemic_class",
                        )
                    )

                for claim_idx, claim in enumerate(c.get("numeric_claims", [])):
                    if not isinstance(claim, dict):
                        continue
                    val = claim.get("value")
                    try:
                        Decimal(str(val))
                    except (InvalidOperation, TypeError):
                        violations.append(
                            ValidationViolation(
                                gate=cls.GATE_NAME,
                                rule="NUMERIC_CLAIM_DECIMAL_REQUIRED",
                                message=f"Numeric claim at conclusions[{idx}].numeric_claims[{claim_idx}] has non-numeric value '{val}'.",
                                field_path=f"conclusions[{idx}].numeric_claims[{claim_idx}].value",
                            )
                        )

        return violations
