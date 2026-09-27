"""
NEXORA ATLAS - Intelligence Engine Domain Models & Contracts
"""

from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.intelligence.constants import RULESET_VERSION
from app.intelligence.types import (
    Severity,
    RiskLevel,
    RuleStatus,
    WasteType,
    AnomalyRuleType,
    EvidenceType,
)


class EvidenceContract(BaseModel):
    """Explicit contract defining required evidence for a detector rule to execute."""
    rule_name: str
    required_fields: List[str]
    min_sample_size: int = 1
    telemetry_source: str = "operational"

    def check(self, data: Dict[str, Any], sample_size: int = 1) -> Tuple[bool, Optional[str]]:
        """Verifies if input data satisfies the evidence contract. Returns (is_satisfied, reason)."""
        if sample_size < self.min_sample_size:
            return (
                False,
                f"Insufficient sample size for {self.rule_name}: required {self.min_sample_size}, got {sample_size}",
            )
        missing = [f for f in self.required_fields if f not in data or data[f] is None]
        if missing:
            return (
                False,
                f"Missing required {self.telemetry_source} telemetry for {self.rule_name}: {', '.join(missing)}",
            )
        return True, None


class EvidenceItem(BaseModel):
    """Structured audit-ready evidence record."""
    type: EvidenceType
    source: str
    metric: str
    value: Any
    comparison: Optional[str] = None
    timestamp: Optional[datetime] = None
    explanation: str


class RuleEvaluationResult(BaseModel):
    """Audit log of rule execution status: EVALUATED vs SKIPPED."""
    rule_id: str
    rule_type: str
    status: RuleStatus
    skip_reason: Optional[str] = None
    findings_count: int = 0


class AnomalyFinding(BaseModel):
    """Deterministic spending anomaly finding."""
    id: str = ""
    account_id: str
    account_name: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    resource_native_id: Optional[str] = None
    service_name: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rule_type: AnomalyRuleType
    observed_cost: Decimal
    baseline_cost: Decimal
    percentage_change: Decimal
    severity: Severity
    confidence_score: Decimal = Field(description="Deterministic evidence strength (0-100)")
    observed_metrics: Dict[str, Any] = Field(default_factory=dict)
    inferred_cause: Optional[str] = None
    inference_details: Dict[str, Any] = Field(default_factory=dict)
    run_id: str = ""
    ruleset_version: str = RULESET_VERSION

    @property
    def anomaly_type(self) -> AnomalyRuleType:
        return self.rule_type

    @property
    def detected_spend(self) -> Decimal:
        return self.observed_cost

    @property
    def expected_spend(self) -> Decimal:
        return self.baseline_cost

    @property
    def percentage_deviation(self) -> Decimal:
        return self.percentage_change

    @property
    def duration_days(self) -> int:
        return int(self.observed_metrics.get("consecutive_days_elevated") or self.observed_metrics.get("consecutive_increase_days", 1))


    @property
    def evidence_json(self) -> Dict[str, Any]:
        return {
            "observed_facts": self.observed_metrics,
            "inferences": self.inference_details,
            "inferred_cause": self.inferred_cause,
            "confidence_score": str(self.confidence_score),
        }


class RecommendationCandidate(BaseModel):
    """Actionable recommendation option with explicit assumptions."""
    title: str
    category: str
    current_configuration: str
    recommended_configuration: str
    estimated_monthly_savings: Decimal
    estimated_annual_savings: Decimal
    confidence_score: Decimal
    risk_level: Union[RiskLevel, str]
    reasoning: str
    assumptions_json: Dict[str, Any] = Field(default_factory=dict)
    evidence_json: Dict[str, Any] = Field(default_factory=dict)
    status: str = "OPEN"


class OpportunityCandidate(BaseModel):
    """Optimization opportunity grouping waste evidence with recommendation candidates."""
    account_id: str
    account_name: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    resource_native_id: Optional[str] = None
    category: str
    waste_type: WasteType
    severity: Severity
    estimated_waste_monthly: Decimal
    evidence_json: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: Decimal = Decimal("90.00")
    recommendations: List[RecommendationCandidate] = Field(default_factory=list)
    status: str = "OPEN"
    run_id: str = ""
    ruleset_version: str = RULESET_VERSION


class IntelligenceRunResult(BaseModel):
    """Top-level immutable result of an intelligence analysis run."""
    run_id: str
    organization_id: str
    ruleset_version: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int = 0
    anomalies_detected: int = 0
    opportunities_found: int = 0
    recommendations_generated: int = 0
    potential_monthly_savings: Decimal = Decimal("0.0000")
    potential_annual_savings: Decimal = Decimal("0.0000")
    rule_evaluations: List[RuleEvaluationResult] = Field(default_factory=list)
    evaluated_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    skipped_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    anomalies: List[AnomalyFinding] = Field(default_factory=list)
    opportunities: List[OpportunityCandidate] = Field(default_factory=list)
    status: str = "COMPLETED"
    summary: Dict[str, Any] = Field(default_factory=dict)

