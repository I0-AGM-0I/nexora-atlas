"""
NEXORA ATLAS - Context Builder (Phase 9)
Orchestrates evidence retrieval, sanitization, budget capping, canonicalization, and hashing.
Produces a mathematically auditable, secure evidence package ready for AI consumption.
"""

from typing import Tuple, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tenant import TenantContext
from app.ai.types import ScopeType, QuestionCategory, DataFreshnessStatus
from app.ai.models import EvidencePackage, EvidenceItem, BoundedContext
from app.ai.retrieval.evidence_retriever import EvidenceRetriever
from app.ai.context.sanitizer import sanitize_evidence_item
from app.ai.context.budget import enforce_budget, apply_context_budget
from app.ai.context.canonicalizer import canonicalize_evidence_package, compute_evidence_hash


class ContextBuilder:
    """
    Builds a secure, sanitized, and canonically hashed EvidencePackage and BoundedContext.
    """

    @classmethod
    async def build_context(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        scope_type: ScopeType,
        scope_id: Optional[str] = None,
        category: QuestionCategory = QuestionCategory.SPEND_OVERVIEW,
        detected_services: Optional[List[str]] = None,
    ) -> Tuple[EvidencePackage, str]:
        """
        1. Retrieves raw domain evidence from authoritative Atlas engines.
        2. Sanitizes all secrets and frames untrusted metadata in <untrusted_metadata>.
        3. Enforces item and token budgets without silent truncation.
        4. Calculates the canonical SHA-256 evidence integrity hash.
        Returns: (sanitized_budgeted_package, evidence_hash)
        """
        raw_package = await EvidenceRetriever.retrieve_evidence(
            session=session,
            tenant=tenant,
            scope_type=scope_type,
            scope_id=scope_id,
            category=category,
            detected_services=detected_services,
        )

        # Sanitize all items across collections
        sanitized_pkg = EvidencePackage(
            scope_type=raw_package.scope_type,
            scope_id=raw_package.scope_id,
            freshness=raw_package.freshness,
            observations=[sanitize_evidence_item(i) for i in raw_package.observations],
            derived_metrics=[sanitize_evidence_item(i) for i in raw_package.derived_metrics],
            inferences=[sanitize_evidence_item(i) for i in raw_package.inferences],
            recommendations=[sanitize_evidence_item(i) for i in raw_package.recommendations],
            scenarios=[sanitize_evidence_item(i) for i in raw_package.scenarios],
            telemetry=[sanitize_evidence_item(i) for i in raw_package.telemetry],
            data_quality=raw_package.data_quality,
            limitations=list(raw_package.limitations),
            is_context_limited=raw_package.is_context_limited,
            evidence_count=raw_package.evidence_count,
        )

        # Apply budget limits
        budgeted_pkg = enforce_budget(sanitized_pkg)

        # Compute deterministic SHA-256 hash
        evidence_hash = compute_evidence_hash(budgeted_pkg)

        return budgeted_pkg, evidence_hash

    @classmethod
    def create_bounded_context(cls, package: EvidencePackage) -> BoundedContext:
        """
        Transforms an EvidencePackage into a formal BoundedContext envelope.
        """
        items = package.all_items()
        canonical_str = canonicalize_evidence_package(package)
        digest = compute_evidence_hash(package)

        return BoundedContext(
            evidence_items=items,
            included_count=len(items),
            excluded_count=0 if not package.is_context_limited else max(0, package.evidence_count - len(items)),
            is_context_limited=package.is_context_limited,
            freshness_status=package.freshness.status if package.freshness else DataFreshnessStatus.UNKNOWN,
            limitations=list(package.limitations),
            canonical_json=canonical_str,
            sha256_hash=digest,
        )
