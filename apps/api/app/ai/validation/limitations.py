"""
NEXORA ATLAS - Gate 8: Limitation Preservation & Freshness (Phase 9 Milestone 4)
Guarantees that material evidence limitations are faithfully represented.
Prevents inventing telemetry when unavailable and mandates qualifying stale data.
"""

from typing import List, Dict, Set
from app.ai.types import EpistemicClass, DataFreshnessStatus
from app.ai.models import EvidencePackage, EvidenceItem
from app.ai.providers.models import AICandidateAnswer
from app.ai.validation.result import ValidationViolation


class LimitationsValidator:
    """
    Gate 8: Verifies that material evidence package limitations and freshness statuses
    are preserved in the candidate explanation without fabrication or minimization.
    """

    GATE_NAME = "GATE_8_LIMITATIONS"

    @classmethod
    def validate(
        cls,
        candidate: AICandidateAnswer,
        evidence_package: EvidencePackage,
    ) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []

        # 1. Missing Telemetry Invariant: If telemetry has NOT_AVAILABLE items,
        # candidate must NOT assert direct factual utilization numbers as OBSERVED or DERIVED.
        not_available_items = [
            item for item in evidence_package.all_items()
            if item.epistemic_class == EpistemicClass.NOT_AVAILABLE
        ]

        if not_available_items:
            for c_idx, concl in enumerate(candidate.conclusions):
                # If conclusion claims to have measured CPU/memory as OBSERVED or DERIVED
                if concl.epistemic_class in (EpistemicClass.OBSERVED, EpistemicClass.DERIVED):
                    for claim in concl.numeric_claims:
                        if claim.unit in ("%", "PERCENT", "PERCENTAGE") and (
                            "cpu" in concl.statement.lower() or "utilization" in concl.statement.lower() or "memory" in concl.statement.lower()
                        ):
                            violations.append(
                                ValidationViolation(
                                    gate=cls.GATE_NAME,
                                    rule="FABRICATED_TELEMETRY_OBSERVATION",
                                    message=(
                                        f"Conclusion at index {c_idx} claims observed utilization of {claim.value}% "
                                        "even though operational telemetry for this resource is NOT_AVAILABLE."
                                    ),
                                    field_path=f"conclusions[{c_idx}].numeric_claims",
                                    claim_value=claim.value,
                                )
                            )

        # 2. Freshness Stale Qualification:
        # If evidence package is STALE, candidate must qualify it in freshness_note or limitations.
        if evidence_package.freshness and evidence_package.freshness.status == DataFreshnessStatus.STALE:
            has_freshness_mention = False
            if candidate.freshness_note and "stale" in candidate.freshness_note.lower():
                has_freshness_mention = True
            elif any("stale" in lim.lower() or "lag" in lim.lower() or "delay" in lim.lower() for lim in candidate.limitations):
                has_freshness_mention = True

            if not has_freshness_mention:
                violations.append(
                    ValidationViolation(
                        gate=cls.GATE_NAME,
                        rule="UNQUALIFIED_STALE_EVIDENCE",
                        message=(
                            "Evidence data is STALE according to Atlas ingestion SLAs, but candidate output "
                            "does not qualify this limitation in freshness_note or limitations."
                        ),
                        field_path="freshness_note",
                    )
                )

        return violations
