"""
NEXORA ATLAS - Retrieval Engine (Phase 9)
Deterministic orchestrator for evidence retrieval, ranking, budgeting, and packaging.

CRITICAL INVARIANTS:
  - 100% deterministic, read-only, tenant-isolated, offline-capable, provider-independent.
  - Zero AI calls, zero embeddings, zero vector databases.
  - Authorization MUST precede retrieval.
  - Requested Scope ∩ Authorized Scope = Effective Retrieval Scope.
"""

from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.services.tenant import TenantContext
from app.ai.types import ScopeType, QuestionCategory, EpistemicClass
from app.ai.models import EvidenceItem, EvidencePackage, DataFreshness
from app.ai.authorization.scope import authorize_scope, AuthorizationScope
from app.ai.questions.classifier import default_classifier, QueryIntent
from app.ai.questions.scope_resolver import ScopeResolver
from app.ai.retrieval.selectors import (
    SpendEvidenceSelector,
    CostDriverEvidenceSelector,
    AnomalyEvidenceSelector,
    ResourceEvidenceSelector,
    TelemetryEvidenceSelector,
    RecommendationEvidenceSelector,
    ScenarioEvidenceSelector,
    ForecastEvidenceSelector,
)
from app.ai.retrieval.freshness import evaluate_package_freshness
from app.ai.retrieval.ranking import rank_evidence_items
from app.ai.context.budget import enforce_budget
from app.ai.context.sanitizer import sanitize_evidence_item
from app.ai.context.canonicalizer import compute_evidence_hash


class RetrievalEngine:
    """
    Deterministic evidence retrieval engine.
    Implements the EvidenceRetrieverContract interface without any external dependencies.
    """

    @classmethod
    async def build_evidence_package(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        question: str,
        scope_type: ScopeType = ScopeType.DASHBOARD,
        scope_id: Optional[str] = None,
    ) -> EvidencePackage:
        """
        Executes the full 12-step deterministic evidence gathering pipeline:
        1. Validate Tenant Authorization Scope
        2. Classify Question (Router only)
        3. Resolve and Intersect Scope
        4. Select Evidence Sources
        5. Retrieve Domain Evidence
        6. Evaluate Freshness
        7. Categorize and Rank Evidence
        8. Construct EvidencePackage
        9. Sanitize Untrusted Content
        10. Enforce Budget Caps (MAX_EVIDENCE_ITEMS = 100)
        11. Generate Deterministic SHA-256 Digest
        12. Return Final Authoritative Package
        """
        # Step 1: Pre-retrieval Tenant Authorization
        auth_result = await authorize_scope(session, tenant, scope_type, scope_id)
        auth_scope = auth_result.authorization_scope or AuthorizationScope.from_tenant(tenant)

        # Step 2: Deterministic Question Classification
        intent: QueryIntent = default_classifier.classify_intent(
            question=question,
            scope_type=scope_type,
            scope_id=scope_id,
        )

        # Step 3: Scope Resolution & Intersection Check
        resolved = ScopeResolver.resolve_scope(
            requested_scope_type=scope_type,
            requested_scope_id=scope_id,
            auth_scope=auth_scope,
            category=intent.category,
        )

        if not resolved.is_authorized:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=resolved.denial_reason or "Requested scope is not authorized for tenant.",
            )

        # Step 4 & 5: Select Evidence Sources & Retrieve Domain Records
        observations: List[EvidenceItem] = []
        derived_metrics: List[EvidenceItem] = []
        inferences: List[EvidenceItem] = []
        recommendations: List[EvidenceItem] = []
        scenarios: List[EvidenceItem] = []
        telemetry: List[EvidenceItem] = []
        limitations: List[str] = []

        eff_scope_type = resolved.scope_type
        eff_scope_id = resolved.scope_id

        # Scope: RESOURCE
        if eff_scope_type == ScopeType.RESOURCE and eff_scope_id:
            res_items = await ResourceEvidenceSelector.select_evidence(session, tenant, eff_scope_id)
            observations.extend(res_items)

            cw_items = await TelemetryEvidenceSelector.select_evidence(session, tenant, eff_scope_id)
            for item in cw_items:
                if item.epistemic_class == EpistemicClass.NOT_AVAILABLE:
                    limitations.append(item.statement)
                else:
                    telemetry.append(item)

            rec_items = await RecommendationEvidenceSelector.select_evidence(
                session, tenant, resource_id=eff_scope_id
            )
            recommendations.extend(rec_items)

        # Scope: RECOMMENDATION
        elif eff_scope_type == ScopeType.RECOMMENDATION and eff_scope_id:
            rec_items = await RecommendationEvidenceSelector.select_evidence(
                session, tenant, recommendation_id=eff_scope_id
            )
            recommendations.extend(rec_items)

        # Scope: SCENARIO
        elif eff_scope_type == ScopeType.SCENARIO and eff_scope_id:
            scen_items = await ScenarioEvidenceSelector.select_evidence(
                session, tenant, scenario_id=eff_scope_id
            )
            scenarios.extend(scen_items)

        # Scope: DASHBOARD / ACCOUNT / SERVICE / General
        else:
            # Spend evidence
            spend_items = await SpendEvidenceSelector.select_evidence(
                session, tenant, eff_scope_type, eff_scope_id
            )
            for item in spend_items:
                if item.epistemic_class == EpistemicClass.DERIVED:
                    derived_metrics.append(item)
                else:
                    observations.append(item)

            # If question is about drivers, anomalies, optimization, or forecast, enrich accordingly
            if intent.category in [QuestionCategory.COST_DRIVER, QuestionCategory.SPEND_CHANGE]:
                driver_items = await CostDriverEvidenceSelector.select_evidence(session, tenant)
                derived_metrics.extend(driver_items)

            if intent.category in [QuestionCategory.ANOMALY, QuestionCategory.SPEND_CHANGE]:
                anom_items = await AnomalyEvidenceSelector.select_evidence(session, tenant)
                observations.extend(anom_items)

            if intent.category in [QuestionCategory.OPTIMIZATION, QuestionCategory.SPEND_CHANGE]:
                rec_items = await RecommendationEvidenceSelector.select_evidence(session, tenant)
                recommendations.extend(rec_items)

            if intent.category == QuestionCategory.SCENARIO:
                scen_items = await ScenarioEvidenceSelector.select_evidence(session, tenant)
                scenarios.extend(scen_items)

            if intent.category == QuestionCategory.FORECAST:
                forecast_items = await ForecastEvidenceSelector.select_evidence(session, tenant)
                scenarios.extend(forecast_items)

        # Step 6: Freshness Assessment
        freshness: DataFreshness = evaluate_package_freshness()

        # Step 7: Construct Initial Unbudgeted Package
        raw_pkg = EvidencePackage(
            scope_type=eff_scope_type,
            scope_id=eff_scope_id,
            freshness=freshness,
            observations=observations,
            derived_metrics=derived_metrics,
            inferences=inferences,
            recommendations=recommendations,
            scenarios=scenarios,
            telemetry=telemetry,
            limitations=limitations,
            evidence_count=len(observations) + len(derived_metrics) + len(inferences) + len(recommendations) + len(scenarios) + len(telemetry),
        )

        # Step 8: Sanitize untrusted metadata & redact secrets across all collections
        sanitized_pkg = EvidencePackage(
            scope_type=raw_pkg.scope_type,
            scope_id=raw_pkg.scope_id,
            freshness=raw_pkg.freshness,
            observations=[sanitize_evidence_item(i) for i in raw_pkg.observations],
            derived_metrics=[sanitize_evidence_item(i) for i in raw_pkg.derived_metrics],
            inferences=[sanitize_evidence_item(i) for i in raw_pkg.inferences],
            recommendations=[sanitize_evidence_item(i) for i in raw_pkg.recommendations],
            scenarios=[sanitize_evidence_item(i) for i in raw_pkg.scenarios],
            telemetry=[sanitize_evidence_item(i) for i in raw_pkg.telemetry],
            data_quality=raw_pkg.data_quality,
            limitations=list(raw_pkg.limitations),
            is_context_limited=raw_pkg.is_context_limited,
            evidence_count=raw_pkg.evidence_count,
        )

        # Step 9: Enforce Context Budget (Ranked preservation, MAX_EVIDENCE_ITEMS = 100)
        budgeted_pkg = enforce_budget(sanitized_pkg)

        # Step 10: Compute Deterministic SHA-256 Digest
        return budgeted_pkg
