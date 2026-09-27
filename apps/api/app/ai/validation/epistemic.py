"""
NEXORA ATLAS - Gate 4: Epistemic Integrity Validation (Phase 9 Milestone 4)
Enforces the strict epistemic boundary hierarchy.
Prohibits the AI from upgrading modeled, projected, or missing evidence into observed facts.
"""

from typing import List, Dict, Set
from app.ai.types import EpistemicClass
from app.ai.models import EvidencePackage, EvidenceItem
from app.ai.providers.models import AICandidateAnswer
from app.ai.validation.result import ValidationViolation
from app.ai.contracts import PROHIBITED_EPISTEMIC_UPGRADES


class EpistemicValidator:
    """
    Gate 4: Verifies epistemic integrity and prohibits epistemic upgrades.
    Conclusions must preserve the epistemic classification of underlying evidence.
    """

    GATE_NAME = "GATE_4_EPISTEMIC"

    @classmethod
    def validate(
        cls,
        candidate: AICandidateAnswer,
        evidence_package: EvidencePackage,
    ) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []
        evidence_map: Dict[str, EvidenceItem] = {item.id: item for item in evidence_package.all_items()}

        for c_idx, concl in enumerate(candidate.conclusions):
            concl_class = concl.epistemic_class

            # Inspect all evidence items referenced by this conclusion
            referenced_items = [
                evidence_map[eid]
                for eid in concl.evidence_ids
                if eid in evidence_map
            ]

            # Also check evidence items referenced by child numeric claims
            for claim in concl.numeric_claims:
                if claim.evidence_id and claim.evidence_id in evidence_map:
                    if evidence_map[claim.evidence_id] not in referenced_items:
                        referenced_items.append(evidence_map[claim.evidence_id])

            for ev_item in referenced_items:
                ev_class = ev_item.epistemic_class

                # Check against prohibited upgrade pairs
                if (concl_class, ev_class) in PROHIBITED_EPISTEMIC_UPGRADES:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="PROHIBITED_EPISTEMIC_UPGRADE",
                            message=(
                                f"Conclusion {c_idx} invalidly upgraded epistemic status to {concl_class.value} "
                                f"from underlying evidence '{ev_item.id}' which is {ev_class.value}."
                            ),
                            evidence_id=ev_item.id,
                            field_path=f"conclusions[{c_idx}].epistemic_class",
                        )
                    )

                # Special check for OBSERVED claiming on INFERRED/PROJECTED/ASSUMED/NOT_AVAILABLE
                if concl_class == EpistemicClass.OBSERVED and ev_class in (
                    EpistemicClass.INFERRED,
                    EpistemicClass.PROJECTED,
                    EpistemicClass.ASSUMED,
                    EpistemicClass.NOT_AVAILABLE,
                ):
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="INVALID_OBSERVED_UPGRADE",
                            message=(
                                f"Conclusion {c_idx} invalidly upgraded epistemic status to OBSERVED "
                                f"from modeled/inferred evidence '{ev_item.id}' ({ev_class.value})."
                            ),
                            evidence_id=ev_item.id,
                            field_path=f"conclusions[{c_idx}].epistemic_class",
                        )
                    )

                # Special check for DERIVED or OBSERVED claiming on PROJECTED
                if concl_class in (EpistemicClass.OBSERVED, EpistemicClass.DERIVED) and ev_class == EpistemicClass.PROJECTED:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="PROJECTED_PRESENTED_AS_FACT",
                            message=(
                                f"Conclusion {c_idx} invalidly presented PROJECTED evidence '{ev_item.id}' "
                                f"as {concl_class.value}."
                            ),
                            evidence_id=ev_item.id,
                            field_path=f"conclusions[{c_idx}].epistemic_class",
                        )
                    )

        return violations
