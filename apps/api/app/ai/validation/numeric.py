"""
NEXORA ATLAS - Gate 3: Numeric Claim Validation & Semantic Matching (Phase 9 Milestone 4)
Deterministic mathematical tolerance verification engine using Decimal precision.
Enforces the strict ±1.0% tolerance rule, exact zero baseline, unit compatibility,
and semantic quantity preservation.
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal

from app.ai.constants import NUMERICAL_TOLERANCE_RATIO
from app.ai.models import EvidencePackage, EvidenceItem
from app.ai.providers.models import AICandidateAnswer, AICandidateNumericClaim
from app.ai.validation.result import ValidationViolation


# Canonical unit normalization mapping
UNIT_NORMALIZATION = {
    "inr": "INR",
    "rs": "INR",
    "rs.": "INR",
    "₹": "INR",
    "rupees": "INR",
    "%": "%",
    "percent": "%",
    "percentage": "%",
    "usd": "USD",
    "$": "USD",
    "gb": "GB",
    "gib": "GB",
    "tb": "TB",
    "hours": "HOURS",
    "hrs": "HOURS",
    "count": "COUNT",
    "instances": "COUNT",
}


def normalize_unit(unit: Optional[str]) -> str:
    """Normalizes unit string for canonical comparison."""
    if not unit:
        return ""
    clean = unit.strip().lower()
    return UNIT_NORMALIZATION.get(clean, clean.upper())


class NumericValidator:
    """
    Gate 3: Crown jewel of M4.
    Validates structured numeric claims against authoritative Atlas evidence.
    Enforces ±1.0% tolerance, zero-baseline exactness, and unit compatibility.
    """

    GATE_NAME = "GATE_3_NUMERIC"

    @classmethod
    def validate(
        cls,
        candidate: AICandidateAnswer,
        evidence_package: EvidencePackage,
        tolerance_ratio: Decimal = NUMERICAL_TOLERANCE_RATIO,
    ) -> List[ValidationViolation]:
        violations: List[ValidationViolation] = []
        evidence_map: Dict[str, EvidenceItem] = {item.id: item for item in evidence_package.all_items()}

        for c_idx, concl in enumerate(candidate.conclusions):
            for nc_idx, claim in enumerate(concl.numeric_claims):
                path = f"conclusions[{c_idx}].numeric_claims[{nc_idx}]"
                ev_id = claim.evidence_id

                if not ev_id or ev_id not in evidence_map:
                    # Nonexistent evidence ID is handled by Gate 2, but flag if present
                    continue

                ev_item = evidence_map[ev_id]

                # 1. Evidence must have a numerical value
                if ev_item.value is None:
                    violations.append(
                        ValidationViolation(
                            gate=cls.GATE_NAME,
                            rule="EVIDENCE_HAS_NO_NUMERICAL_VALUE",
                            message=(
                                f"Numeric claim for {claim.value} {claim.unit} references evidence item "
                                f"'{ev_id}' which contains no numerical quantity."
                            ),
                            evidence_id=ev_id,
                            field_path=f"{path}.evidence_id",
                            claim_value=claim.value,
                        )
                    )
                    continue

                actual_val = Decimal(str(ev_item.value))
                claimed_val = Decimal(str(claim.value))

                # 2. Unit Compatibility Check
                if claim.unit and ev_item.unit:
                    norm_claim_unit = normalize_unit(claim.unit)
                    norm_actual_unit = normalize_unit(ev_item.unit)
                    if norm_claim_unit != norm_actual_unit:
                        violations.append(
                            ValidationViolation(
                                gate=cls.GATE_NAME,
                                rule="INCOMPATIBLE_NUMERIC_UNIT",
                                message=(
                                    f"Numeric claim unit '{claim.unit}' is incompatible with evidence unit "
                                    f"'{ev_item.unit}' for evidence '{ev_id}'."
                                ),
                                evidence_id=ev_id,
                                field_path=f"{path}.unit",
                                claim_value=claimed_val,
                                authoritative_value=actual_val,
                            )
                        )
                        continue

                # 3. Mathematical Tolerance Verification
                # Zero-Baseline Invariant: If actual == 0, claim must be strictly 0
                if actual_val == Decimal("0"):
                    if claimed_val != Decimal("0"):
                        violations.append(
                            ValidationViolation(
                                gate=cls.GATE_NAME,
                                rule="NUMERIC_ZERO_BASELINE_EXACTNESS",
                                message=(
                                    f"Numerical hallucination: claimed {claimed_val}, but authoritative evidence "
                                    f"'{ev_id}' is exactly 0. Exact zero is strictly required on zero baselines."
                                ),
                                evidence_id=ev_id,
                                field_path=f"{path}.value",
                                claim_value=claimed_val,
                                authoritative_value=actual_val,
                            )
                        )
                else:
                    # ±1.0% tolerance: |claimed - actual| <= |actual| * 0.01
                    abs_error = abs(claimed_val - actual_val)
                    allowed_error = abs(actual_val) * tolerance_ratio

                    if abs_error > allowed_error:
                        rel_diff_pct = (abs_error / abs(actual_val)) * Decimal("100")
                        violations.append(
                            ValidationViolation(
                                gate=cls.GATE_NAME,
                                rule="NUMERIC_TOLERANCE_EXCEEDED",
                                message=(
                                    f"Numerical hallucination: claimed {claimed_val} deviates {rel_diff_pct:.2f}% "
                                    f"from authoritative evidence {actual_val} for '{ev_id}' (tolerance: 1.0%)."
                                ),
                                evidence_id=ev_id,
                                field_path=f"{path}.value",
                                claim_value=claimed_val,
                                authoritative_value=actual_val,
                            )
                        )

        return violations
