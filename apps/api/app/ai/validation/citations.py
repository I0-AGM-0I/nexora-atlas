"""
NEXORA ATLAS - Gate 5: Citation Integrity & Completeness (Phase 9 Milestone 4)
Verifies citation grounding and builds a deterministic audit graph.
Ensures factual statements and numeric assertions cite supporting evidence.
"""

from typing import List, Dict, Set
from app.ai.types import EpistemicClass
from app.ai.models import EvidencePackage, EvidenceItem
from app.ai.providers.models import AICandidateAnswer, AICandidateConclusion
from app.ai.validation.result import ValidationViolation


# Factual keywords indicating an assertion about Atlas data rather than general advice
FACTUAL_INDICATORS = {
    "cost", "spend", "surge", "increase", "decrease", "grew", "growth",
    "driver", "consumed", "utilized", "utilization", "cpu", "memory",
    "iops", "instance", "cluster", "account", "service", "₹", "$", "%",
    "recommendation", "downsize", "savings", "anomaly", "detected"
}


def is_factual_conclusion(concl: AICandidateConclusion) -> bool:
    """
    Determines whether a conclusion asserts factual Atlas state requiring evidence citations.
    Any conclusion with numeric claims or an epistemic class other than ASSUMED
    is treated as a factual assertion.
    """
    if len(concl.numeric_claims) > 0:
        return True
    if concl.epistemic_class in (EpistemicClass.OBSERVED, EpistemicClass.DERIVED):
        return True

    text_lower = concl.statement.lower()
    return any(indicator in text_lower for indicator in FACTUAL_INDICATORS)


class CitationValidator:
    """
    Gate 5: Verifies that factual conclusions cite supporting evidence.
    Constructs and verifies the deterministic citation audit graph.
    """

    GATE_NAME = "GATE_5_CITATION"

    @classmethod
    def validate(
        cls,
        candidate: AICandidateAnswer,
        evidence_package: EvidencePackage,
    ) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []

        for c_idx, concl in enumerate(candidate.conclusions):
            path = f"conclusions[{c_idx}]"

            # 1. Factual assertions must cite at least one evidence ID
            if is_factual_conclusion(concl) and len(concl.evidence_ids) == 0:
                violations.append(
                    ValidationViolation(
                        gate=cls.GATE_NAME,
                        rule="UNSUPPORTED_FACTUAL_CLAIM",
                        message=(
                            f"Conclusion at index {c_idx} ('{concl.statement[:60]}...') makes factual Atlas "
                            f"assertions but contains zero supporting evidence citations."
                        ),
                        field_path=f"{path}.evidence_ids",
                    )
                )

            # 2. Every numeric claim must reference an evidence ID
            for nc_idx, claim in enumerate(concl.numeric_claims):
                if not claim.evidence_id:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="NUMERIC_CLAIM_MISSING_CITATION",
                            message=(
                                f"Numeric claim for {claim.value} {claim.unit} at {path}.numeric_claims[{nc_idx}] "
                                f"does not cite an evidence ID."
                            ),
                            field_path=f"{path}.numeric_claims[{nc_idx}].evidence_id",
                            claim_value=claim.value,
                        )
                    )

        return violations
