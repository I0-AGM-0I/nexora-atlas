"""
NEXORA ATLAS - Master Response Validator (Phase 9 Milestone 4)
Orchestrates the 8 deterministic validation gates.
Maintains the strict type-level trust boundary:
AICandidateAnswer (untrusted) -> ResponseValidator -> AIAnswer (verified)
"""

from typing import Union, Dict, Any, List, Optional
from decimal import Decimal

from app.ai.types import EpistemicClass
from app.ai.models import (
    EvidencePackage,
    AIAnswer,
    AIConclusion,
    NumericClaim,
    AICitation,
)
from app.ai.providers.models import (
    AICandidateAnswer,
    AICandidateConclusion,
    AICandidateNumericClaim,
)
from app.ai.validation.result import (
    ValidationStatus,
    ValidationViolation,
    ValidationResult,
    VALIDATOR_VERSION,
)
from app.ai.validation.schema import SchemaValidator
from app.ai.validation.evidence import EvidenceValidator
from app.ai.validation.numeric import NumericValidator
from app.ai.validation.epistemic import EpistemicValidator
from app.ai.validation.citations import CitationValidator
from app.ai.validation.security import SecurityValidator
from app.ai.validation.limitations import LimitationsValidator


class ResponseValidator:
    """
    Master Response Validator for NEXORA ATLAS.
    Executes Gates 1 through 8 in strict sequence.
    Constructs an AIAnswer ONLY if all gates pass with zero violations.
    """

    VERSION = VALIDATOR_VERSION

    @classmethod
    def validate(
        cls,
        candidate: Union[AICandidateAnswer, Dict[str, Any]],
        evidence_package: EvidencePackage,
        evidence_hash: Optional[str] = None,
    ) -> ValidationResult:
        all_violations: List[ValidationViolation] = []
        eff_hash = evidence_hash or evidence_package.compute_hash()

        # Gate 6 & 7: Check Security & Confidence first (reject hostile payloads early)
        sec_violations = SecurityValidator.validate(candidate)
        if sec_violations:
            return ValidationResult(
                status=ValidationStatus.SECURITY_VIOLATION,
                is_valid=False,
                verified_answer=None,
                violations=sec_violations,
                validation_version=cls.VERSION,
                evidence_hash=eff_hash,
            )

        # Gate 1: Schema Validation
        schema_violations = SchemaValidator.validate(candidate)
        if schema_violations:
            return ValidationResult(
                status=ValidationStatus.INVALID_SCHEMA,
                is_valid=False,
                verified_answer=None,
                violations=schema_violations,
                validation_version=cls.VERSION,
                evidence_hash=eff_hash,
            )

        # Normalize raw dictionary into AICandidateAnswer if needed
        cand_obj: AICandidateAnswer
        if isinstance(candidate, AICandidateAnswer):
            cand_obj = candidate
        else:
            cand_obj = cls._dict_to_candidate_obj(candidate)

        # Gate 2: Evidence-ID Resolution
        evidence_violations = EvidenceValidator.validate(cand_obj, evidence_package)
        all_violations.extend(evidence_violations)

        # Gate 4: Epistemic Integrity
        epistemic_violations = EpistemicValidator.validate(cand_obj, evidence_package)
        all_violations.extend(epistemic_violations)

        # Gate 3: Numeric Claim Validation & Semantic Matching
        numeric_violations = NumericValidator.validate(cand_obj, evidence_package)
        all_violations.extend(numeric_violations)

        # Gate 5: Citation Integrity & Completeness
        citation_violations = CitationValidator.validate(cand_obj, evidence_package)
        all_violations.extend(citation_violations)

        # Gate 8: Limitation Preservation & Freshness
        limitations_violations = LimitationsValidator.validate(cand_obj, evidence_package)
        all_violations.extend(limitations_violations)

        # Evaluate overall outcome
        if all_violations:
            primary_status = cls._determine_primary_status(
                evidence_violations=evidence_violations,
                epistemic_violations=epistemic_violations,
                numeric_violations=numeric_violations,
                citation_violations=citation_violations,
                limitations_violations=limitations_violations,
            )
            return ValidationResult(
                status=primary_status,
                is_valid=False,
                verified_answer=None,
                violations=all_violations,
                validation_version=cls.VERSION,
                evidence_hash=eff_hash,
            )

        # Construct VERIFIED AIAnswer
        verified_answer, val_numeric_claims, val_evidence_ids = cls._construct_verified_answer(cand_obj)

        return ValidationResult(
            status=ValidationStatus.VALID,
            is_valid=True,
            verified_answer=verified_answer,
            violations=[],
            validated_numeric_claims=val_numeric_claims,
            validated_evidence_ids=val_evidence_ids,
            validation_version=cls.VERSION,
            evidence_hash=eff_hash,
            validator_metadata={
                "conclusions_count": len(verified_answer.conclusions),
                "numeric_claims_count": len(val_numeric_claims),
                "evidence_citations_count": len(val_evidence_ids),
            },
        )

    @classmethod
    def _construct_verified_answer(
        cls,
        cand: AICandidateAnswer,
    ) -> tuple[AIAnswer, List[NumericClaim], List[str]]:
        """Constructs authoritative AIAnswer from an untrusted candidate after all gates pass."""
        validated_numeric_claims: List[NumericClaim] = []
        validated_evidence_ids: List[str] = []

        conclusions: List[AIConclusion] = []
        for c in cand.conclusions:
            claims: List[NumericClaim] = []
            for nc in c.numeric_claims:
                claim_item = NumericClaim(
                    value=nc.value,
                    unit=nc.unit,
                    evidence_id=nc.evidence_id,
                    evidence_ids=[nc.evidence_id] if nc.evidence_id else [],
                )
                claims.append(claim_item)
                validated_numeric_claims.append(claim_item)

            for eid in c.evidence_ids:
                if eid not in validated_evidence_ids:
                    validated_evidence_ids.append(eid)

            conclusions.append(
                AIConclusion(
                    statement=c.statement,
                    epistemic_class=c.epistemic_class,
                    evidence_ids=c.evidence_ids,
                    numeric_claims=claims,
                )
            )

        citations: List[AICitation] = []
        for cit in cand.cited_entities:
            citations.append(
                AICitation(
                    id=cit.id,
                    title=cit.title,
                    entity_type=cit.entity_type,
                    entity_id=cit.entity_id,
                    link_path=cit.link_path or "",
                )
            )

        answer = AIAnswer(
            summary=cand.summary,
            answer=cand.answer,
            conclusions=conclusions,
            limitations=list(cand.limitations),
            recommended_next_steps=list(cand.recommended_next_steps),
            cited_entities=citations,
            epistemic_notes=list(cand.epistemic_notes),
            freshness_note=cand.freshness_note,
        )

        return answer, validated_numeric_claims, validated_evidence_ids

    @classmethod
    def _determine_primary_status(
        cls,
        evidence_violations: List[ValidationViolation],
        epistemic_violations: List[ValidationViolation],
        numeric_violations: List[ValidationViolation],
        citation_violations: List[ValidationViolation],
        limitations_violations: List[ValidationViolation],
    ) -> ValidationStatus:
        """Determines the primary failure status based on gate priority."""
        if evidence_violations:
            return ValidationStatus.INVALID_EVIDENCE
        if limitations_violations:
            return ValidationStatus.UNSUPPORTED_CLAIM
        if numeric_violations:
            return ValidationStatus.INVALID_NUMERIC_CLAIM
        if epistemic_violations:
            return ValidationStatus.INVALID_EPISTEMIC_CLASS
        if citation_violations:
            return ValidationStatus.INVALID_CITATION
        return ValidationStatus.UNSUPPORTED_CLAIM

    @classmethod
    def _dict_to_candidate_obj(cls, data: Dict[str, Any]) -> AICandidateAnswer:
        """Coerces a raw dictionary to an AICandidateAnswer structure."""
        conclusions: List[AICandidateConclusion] = []
        for c in data.get("conclusions", []):
            if isinstance(c, dict):
                claims: List[AICandidateNumericClaim] = []
                for claim in c.get("numeric_claims", []):
                    if isinstance(claim, dict):
                        claims.append(
                            AICandidateNumericClaim(
                                value=Decimal(str(claim.get("value", 0))),
                                unit=str(claim.get("unit", "")),
                                evidence_id=claim.get("evidence_id") or (claim.get("evidence_ids", [None])[0] if claim.get("evidence_ids") else None),
                            )
                        )
                ep_raw = str(c.get("epistemic_class", "INFERRED")).upper()
                try:
                    ep_class = EpistemicClass(ep_raw)
                except ValueError:
                    ep_class = EpistemicClass.INFERRED

                conclusions.append(
                    AICandidateConclusion(
                        statement=str(c.get("statement", "")),
                        epistemic_class=ep_class,
                        evidence_ids=[str(i) for i in c.get("evidence_ids", [])],
                        numeric_claims=claims,
                    )
                )

        return AICandidateAnswer(
            summary=str(data.get("summary", "")),
            answer=str(data.get("answer", "")),
            conclusions=conclusions,
            limitations=[str(l) for l in data.get("limitations", [])],
            recommended_next_steps=[str(s) for s in data.get("recommended_next_steps", [])],
            cited_entities=[],
            epistemic_notes=[str(n) for n in data.get("epistemic_notes", [])],
            freshness_note=data.get("freshness_note"),
            raw_json=data,
        )


# Backward-compatible alias for existing M1/M2/M3 callers
class AIResponseValidator:
    """Legacy interface adapter routing directly to ResponseValidator."""

    @classmethod
    def validate(
        cls,
        raw_payload: Union[AICandidateAnswer, Dict[str, Any]],
        evidence_package: EvidencePackage,
    ) -> ValidationResult:
        return ResponseValidator.validate(raw_payload, evidence_package)
