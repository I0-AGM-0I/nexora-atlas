"""
NEXORA ATLAS - Gate 2: Evidence-ID Validation (Phase 9 Milestone 4)
Ensures every evidence ID cited by a candidate answer resolves strictly against
the authorized EvidencePackage. Rejects fabricated or cross-tenant IDs.
"""

from typing import List, Set, Dict, Any, Union
from app.ai.models import EvidencePackage, EvidenceItem
from app.ai.providers.models import AICandidateAnswer
from app.ai.validation.result import ValidationViolation


class EvidenceValidator:
    """
    Gate 2: Verifies that every cited evidence ID exists in the authorized evidence package.
    The AI cannot create evidence or cite IDs from other scopes/tenants.
    """

    GATE_NAME = "GATE_2_EVIDENCE"

    @classmethod
    def validate(
        cls,
        candidate: AICandidateAnswer,
        evidence_package: EvidencePackage,
    ) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []

        valid_evidence_ids: Set[str] = {item.id for item in evidence_package.all_items()}

        # 1. Check conclusion evidence_ids
        for c_idx, concl in enumerate(candidate.conclusions):
            for eid in concl.evidence_ids:
                if eid not in valid_evidence_ids:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="NONEXISTENT_EVIDENCE_ID",
                            message=f"Conclusion {c_idx} cites nonexistent evidence_id '{eid}'.",
                            evidence_id=eid,
                            field_path=f"conclusions[{c_idx}].evidence_ids",
                        )
                    )

            # 2. Check numeric claims evidence_ids
            for nc_idx, claim in enumerate(concl.numeric_claims):
                target_id = claim.evidence_id
                if not target_id:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="NUMERIC_CLAIM_MISSING_EVIDENCE_ID",
                            message=f"Numeric claim at conclusions[{c_idx}].numeric_claims[{nc_idx}] does not specify an evidence_id.",
                            field_path=f"conclusions[{c_idx}].numeric_claims[{nc_idx}].evidence_id",
                        )
                    )
                elif target_id not in valid_evidence_ids:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="NONEXISTENT_EVIDENCE_ID",
                            message=(
                                f"Numeric claim for {claim.value} {claim.unit} references nonexistent "
                                f"or unauthorized evidence_id '{target_id}'."
                            ),
                            evidence_id=target_id,
                            field_path=f"conclusions[{c_idx}].numeric_claims[{nc_idx}].evidence_id",
                            claim_value=claim.value,
                        )
                    )

        # 3. Check cited entities if they reference an evidence ID
        for ce_idx, cit in enumerate(candidate.cited_entities):
            if cit.id and cit.id.startswith("ev-") and cit.id not in valid_evidence_ids:
                violations.append(
                    ValidationViolation(
                        gate=cls.GATE_NAME,
                        rule="NONEXISTENT_EVIDENCE_ID",
                        message=f"Cited entity at index {ce_idx} references nonexistent evidence_id '{cit.id}'.",
                        evidence_id=cit.id,
                        field_path=f"cited_entities[{ce_idx}].id",
                    )
                )

        return violations
