"""
NEXORA ATLAS - Waste Detection Rules with Strict Evidence Contracts
Enforces gating: if required operational telemetry is missing, rules produce SKIPPED
with explicit reasons, preventing hallucinated waste findings.
"""

from decimal import Decimal
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone
import uuid

from app.intelligence.constants import (
    RULESET_VERSION,
    UNATTACHED_STORAGE_MIN_DAYS,
    IDLE_CPU_THRESHOLD_PCT,
    IDLE_MEMORY_THRESHOLD_PCT,
    OVERSIZED_CPU_THRESHOLD_PCT,
    IDLE_DB_MAX_CONNECTIONS,
    IDLE_DB_MIN_DAYS,
    UNASSOCIATED_EIP_MIN_DAYS,
    MIN_TELEMETRY_COVERAGE_FOR_RIGHTSIZING,
    HIGH_MEMORY_CONSTRAINED_THRESHOLD_PCT,
)
from app.intelligence.types import WasteType, Severity, RuleStatus
from app.intelligence.models import EvidenceContract, OpportunityCandidate, RecommendationCandidate, RuleEvaluationResult
from app.intelligence.waste.calculators import (
    calculate_unattached_storage_waste,
    calculate_off_hours_idle_waste,
    calculate_gp3_migration_waste,
    calculate_rightsizing_waste,
)


class UnattachedVolumeRule:
    """Core Rule: Detects unattached EBS block storage volumes."""
    rule_id = "WASTE-RULE-UNATTACHED-VOLUME"
    waste_type = WasteType.UNATTACHED_VOLUME
    category = "STORAGE"
    contract = EvidenceContract(
        rule_name="UnattachedVolumeRule",
        required_fields=["volume_status", "days_unattached"],
        min_sample_size=1,
        telemetry_source="operational",
    )

    @classmethod
    def evaluate(
        cls,
        resource: Dict[str, Any],
        monthly_cost: Decimal,
        account_name: str,
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[OpportunityCandidate]]:
        specs = resource.get("specs_json") or {}
        is_satisfied, reason = cls.contract.check(specs)
        if not is_satisfied:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=reason,
                    findings_count=0,
                ),
                None,
            )

        status = str(specs.get("volume_status", "")).upper()
        days_unattached = int(specs.get("days_unattached", 0))

        if status in ("AVAILABLE", "UNATTACHED") and days_unattached >= UNATTACHED_STORAGE_MIN_DAYS:
            waste, assumptions = calculate_unattached_storage_waste(monthly_cost, days_unattached)
            rec = RecommendationCandidate(
                title="Snapshot and Delete Unattached EBS Volume",
                category="STORAGE",
                current_configuration=f"{specs.get('size_gb', 'Unknown')} GB {specs.get('volume_type', 'gp2')} detached storage",
                recommended_configuration="Retain final snapshot and delete unattached volume",
                estimated_monthly_savings=waste,
                estimated_annual_savings=waste * Decimal("12"),
                confidence_score=Decimal("98.00"),
                risk_level="LOW",
                reasoning=f"Volume has been detached for {days_unattached} consecutive days with zero I/O operations.",
                assumptions_json=assumptions,
                evidence_json={"days_unattached": days_unattached, "volume_status": status},
            )

            opp = OpportunityCandidate(
                account_id=resource["account_id"],
                account_name=account_name,
                resource_id=resource["id"],
                resource_name=resource.get("name"),
                resource_native_id=resource.get("native_id"),
                category=cls.category,
                waste_type=cls.waste_type,
                severity=Severity.MEDIUM if waste < Decimal("30000.0") else Severity.HIGH,
                estimated_waste_monthly=waste,
                evidence_json={
                    "unattached_duration_days": days_unattached,
                    "volume_status": status,
                    "size_gb": specs.get("size_gb"),
                    "volume_type": specs.get("volume_type"),
                    "assumptions": assumptions,
                },
                confidence_score=Decimal("98.00"),
                recommendations=[rec],
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                opp,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.waste_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )


class OversizedInstanceRule:
    """Core Rule: Detects compute instances with sustained low CPU/memory relative to capacity."""
    rule_id = "WASTE-RULE-OVERSIZED-INSTANCE"
    waste_type = WasteType.OVERSIZED_INSTANCE
    category = "COMPUTE"
    contract = EvidenceContract(
        rule_name="OversizedInstanceRule",
        required_fields=["p95_cpu_utilization_pct", "instance_type"],
        min_sample_size=1,
        telemetry_source="operational",
    )

    @classmethod
    def evaluate(
        cls,
        resource: Dict[str, Any],
        monthly_cost: Decimal,
        account_name: str,
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[OpportunityCandidate]]:
        specs = resource.get("specs_json") or {}
        is_satisfied, reason = cls.contract.check(specs)
        if not is_satisfied:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=reason,
                    findings_count=0,
                ),
                None,
            )

        # 1. Telemetry Coverage Gate (Correction 12)
        if specs.get("telemetry_coverage_ratio") is not None:
            cov = Decimal(str(specs["telemetry_coverage_ratio"]))
            if cov < MIN_TELEMETRY_COVERAGE_FOR_RIGHTSIZING:
                return (
                    RuleEvaluationResult(
                        rule_id=cls.rule_id,
                        rule_type=cls.waste_type.value,
                        status=RuleStatus.SKIPPED,
                        skip_reason=f"Insufficient telemetry coverage: {cov * Decimal('100'):.1f}% < {MIN_TELEMETRY_COVERAGE_FOR_RIGHTSIZING * Decimal('100'):.0f}% minimum required for compute rightsizing",
                        findings_count=0,
                    ),
                    None,
                )

        p95_cpu = Decimal(str(specs["p95_cpu_utilization_pct"]))
        instance_type = str(specs["instance_type"])
        is_large_tier = any(tier in instance_type for tier in ["4xlarge", "2xlarge", "xlarge"])

        # 2. Memory Constrained Check (Correction 20 - Resource E)
        p95_mem = None
        if specs.get("p95_memory_utilization_pct") is not None:
            try:
                p95_mem = Decimal(str(specs["p95_memory_utilization_pct"]))
            except Exception:
                p95_mem = None

        if p95_mem is not None and p95_mem >= HIGH_MEMORY_CONSTRAINED_THRESHOLD_PCT:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=f"High memory constraint: p95 memory utilization {p95_mem}% >= {HIGH_MEMORY_CONSTRAINED_THRESHOLD_PCT}% precludes compute downsizing (insufficient compute headroom)",
                    findings_count=0,
                ),
                None,
            )

        if is_large_tier and p95_cpu < OVERSIZED_CPU_THRESHOLD_PCT:
            # 3. Multi-dimensional compute evidence: adjust confidence if memory missing (Correction 13)
            memory_missing = p95_mem is None or specs.get("memory_sufficiency") == "NOT_CONFIGURED"
            confidence = Decimal("80.00") if memory_missing else Decimal("94.00")

            # Conservative downsize target: 1/4 size (e.g. 4xlarge -> large)
            target_cost = (monthly_cost * Decimal("0.25")).quantize(Decimal("0.0001"))
            waste, assumptions = calculate_rightsizing_waste(monthly_cost, target_cost, downsize_ratio="4:1")

            if memory_missing:
                assumptions["memory_telemetry"] = "NOT_CONFIGURED via CloudWatch agent; validate memory prior to modification"

            evidence: Dict[str, Any] = {
                "p95_cpu_utilization_pct": str(p95_cpu),
                "instance_type": instance_type,
                "assumptions": assumptions,
            }
            if p95_mem is not None:
                evidence["p95_memory_utilization_pct"] = str(p95_mem)
            if specs.get("telemetry_coverage_ratio") is not None:
                evidence["telemetry_coverage_ratio"] = str(specs["telemetry_coverage_ratio"])

            epistemic_reasoning = (
                f"Observed utilization is consistently low relative to current instance configuration, "
                f"providing evidence for a rightsizing opportunity. Peak CPU demand observed at {p95_cpu}%."
            )
            if memory_missing:
                epistemic_reasoning += " Note: Memory telemetry not configured; rightsizing confidence discounted."

            recs: List[RecommendationCandidate] = [
                RecommendationCandidate(
                    title=f"Downsize {instance_type} to m5.large",
                    category="COMPUTE",
                    current_configuration=f"{instance_type} (p95 CPU: {p95_cpu}%)",
                    recommended_configuration="m5.large (2 vCPU, 8 GB RAM)",
                    estimated_monthly_savings=waste,
                    estimated_annual_savings=waste * Decimal("12"),
                    confidence_score=confidence,
                    risk_level="LOW" if not memory_missing else "MEDIUM",
                    reasoning=epistemic_reasoning,
                    assumptions_json=assumptions,
                    evidence_json=evidence,
                ),
                # Defensible second option: Modernization to Graviton ARM64
                RecommendationCandidate(
                    title=f"Migrate {instance_type} to Graviton c7g.xlarge",
                    category="COMPUTE",
                    current_configuration=f"{instance_type} (x86_64)",
                    recommended_configuration="c7g.xlarge (4 vCPU, 8 GB RAM, ARM64)",
                    estimated_monthly_savings=(waste * Decimal("1.15")).quantize(Decimal("0.0001")),
                    estimated_annual_savings=(waste * Decimal("1.15") * Decimal("12")).quantize(Decimal("0.0001")),
                    confidence_score=(confidence - Decimal("10.00")),
                    risk_level="MEDIUM",
                    reasoning="ARM64 Graviton instances deliver higher price-performance; requires container architecture validation.",
                    assumptions_json={"architecture_switch": "x86_64 -> arm64", "base_savings": str(waste)},
                    evidence_json={"p95_cpu_pct": str(p95_cpu)},
                ),
            ]

            opp = OpportunityCandidate(
                account_id=resource["account_id"],
                account_name=account_name,
                resource_id=resource["id"],
                resource_name=resource.get("name"),
                resource_native_id=resource.get("native_id"),
                category=cls.category,
                waste_type=cls.waste_type,
                severity=Severity.HIGH if waste >= Decimal("50000.0") else Severity.MEDIUM,
                estimated_waste_monthly=waste,
                evidence_json=evidence,
                confidence_score=confidence,
                recommendations=recs,
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                opp,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.waste_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )


class OffHoursIdleRule:
    """Conditional Rule: Detects non-production compute running 24/7 with zero off-hours activity."""
    rule_id = "WASTE-RULE-OFF-HOURS-IDLE"
    waste_type = WasteType.OFF_HOURS_IDLE
    category = "COMPUTE"
    contract = EvidenceContract(
        rule_name="OffHoursIdleRule",
        required_fields=["running_hours_per_week", "observed_off_hours_cpu_pct"],
        min_sample_size=1,
        telemetry_source="operational",
    )

    @classmethod
    def evaluate(
        cls,
        resource: Dict[str, Any],
        monthly_cost: Decimal,
        account_name: str,
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[OpportunityCandidate]]:
        specs = resource.get("specs_json") or {}
        is_satisfied, reason = cls.contract.check(specs)
        if not is_satisfied:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=reason,
                    findings_count=0,
                ),
                None,
            )

        running_hours = int(specs["running_hours_per_week"])
        off_hours_cpu = Decimal(str(specs["observed_off_hours_cpu_pct"]))
        is_non_prod = "dev" in account_name.lower() or "staging" in account_name.lower() or "dev" in str(resource.get("name", "")).lower()

        if is_non_prod and running_hours >= 168 and off_hours_cpu < Decimal("2.0"):
            waste, assumptions = calculate_off_hours_idle_waste(monthly_cost)
            rec = RecommendationCandidate(
                title="Implement Off-Hours Automated Shutdown for Dev Instances",
                category="COMPUTE",
                current_configuration="Running 24/7 (720 hrs/month)",
                recommended_configuration="Automated schedule: Mon–Fri 09:00–18:00 IST (180 hrs/month)",
                estimated_monthly_savings=waste,
                estimated_annual_savings=waste * Decimal("12"),
                confidence_score=Decimal("96.00"),
                risk_level="LOW",
                reasoning="Off-hours CPU under 2.0% confirms zero active developer utilization outside business hours.",
                assumptions_json=assumptions,
                evidence_json={"off_hours_cpu_pct": str(off_hours_cpu), "running_hours_per_week": running_hours},
            )

            opp = OpportunityCandidate(
                account_id=resource["account_id"],
                account_name=account_name,
                resource_id=resource["id"],
                resource_name=resource.get("name"),
                resource_native_id=resource.get("native_id"),
                category=cls.category,
                waste_type=cls.waste_type,
                severity=Severity.HIGH if waste >= Decimal("50000.0") else Severity.MEDIUM,
                estimated_waste_monthly=waste,
                evidence_json={
                    "running_hours_per_week": running_hours,
                    "observed_off_hours_cpu_pct": str(off_hours_cpu),
                    "assumptions": assumptions,
                },
                confidence_score=Decimal("96.00"),
                recommendations=[rec],
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                opp,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.waste_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )


class IdleDatabaseRule:
    """Conditional Rule: Detects databases with 0 active client connections and high idle ratio."""
    rule_id = "WASTE-RULE-IDLE-DATABASE"
    waste_type = WasteType.IDLE_DATABASE
    category = "DATABASE"
    contract = EvidenceContract(
        rule_name="IdleDatabaseRule",
        required_fields=["active_client_connections", "idle_duration_pct"],
        min_sample_size=1,
        telemetry_source="operational",
    )

    @classmethod
    def evaluate(
        cls,
        resource: Dict[str, Any],
        monthly_cost: Decimal,
        account_name: str,
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[OpportunityCandidate]]:
        specs = resource.get("specs_json") or {}
        is_satisfied, reason = cls.contract.check(specs)
        if not is_satisfied:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=reason,
                    findings_count=0,
                ),
                None,
            )

        # Multi-AZ preservation: Multi-AZ databases indicate HA production systems; low activity does not permit decommissioning (Correction 10)
        is_multi_az = specs.get("multi_az") is True or specs.get("is_multi_az") is True or str(specs.get("multi_az", "")).lower() == "true"
        if is_multi_az:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason="Multi-AZ redundancy indicates high-availability production database; low activity does not permit decommissioning",
                    findings_count=0,
                ),
                None,
            )

        connections = int(specs["active_client_connections"])
        idle_pct = Decimal(str(specs["idle_duration_pct"]))

        if connections <= IDLE_DB_MAX_CONNECTIONS and idle_pct >= Decimal("80.0"):
            waste = monthly_cost.quantize(Decimal("0.0001"))
            rec = RecommendationCandidate(
                title="Evaluate Low Activity Database",
                category="DATABASE",
                current_configuration=f"Continuously running {specs.get('instance_class', 'RDS database')}",
                recommended_configuration="Verify scheduled jobs and evaluate pause or consolidation during non-testing cycles",
                estimated_monthly_savings=waste,
                estimated_annual_savings=waste * Decimal("12"),
                confidence_score=Decimal("92.00"),
                risk_level="LOW",
                reasoning=f"Database exhibits low activity (active connections: {connections}, idle duration: {idle_pct}%). Evidence warrants operational review; verify downstream consumers before pausing.",
                assumptions_json={"waste_ratio": "1.00", "safe_for_dev": True, "autonomous_authority": False},
                evidence_json={"active_connections": connections, "idle_duration_pct": str(idle_pct), "multi_az": False},
            )

            opp = OpportunityCandidate(
                account_id=resource["account_id"],
                account_name=account_name,
                resource_id=resource["id"],
                resource_name=resource.get("name"),
                resource_native_id=resource.get("native_id"),
                category=cls.category,
                waste_type=cls.waste_type,
                severity=Severity.MEDIUM,
                estimated_waste_monthly=waste,
                evidence_json={
                    "active_client_connections": connections,
                    "idle_duration_pct": str(idle_pct),
                },
                confidence_score=Decimal("92.00"),
                recommendations=[rec],
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                opp,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.waste_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )


class LegacyStorageTierRule:
    """Conditional Rule: Detects legacy gp2 EBS volumes that can migrate to gp3 for 20% savings."""
    rule_id = "WASTE-RULE-LEGACY-STORAGE-TIER"
    waste_type = WasteType.LEGACY_STORAGE_TIER
    category = "STORAGE"
    contract = EvidenceContract(
        rule_name="LegacyStorageTierRule",
        required_fields=["volume_type"],
        min_sample_size=1,
        telemetry_source="operational",
    )

    @classmethod
    def evaluate(
        cls,
        resource: Dict[str, Any],
        monthly_cost: Decimal,
        account_name: str,
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[OpportunityCandidate]]:
        specs = resource.get("specs_json") or {}
        is_satisfied, reason = cls.contract.check(specs)
        if not is_satisfied:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=reason,
                    findings_count=0,
                ),
                None,
            )

        v_type = str(specs.get("volume_type", "")).lower()
        if v_type == "gp2":
            waste, assumptions = calculate_gp3_migration_waste(monthly_cost)
            rec = RecommendationCandidate(
                title="Migrate EBS Volume from gp2 to gp3",
                category="STORAGE",
                current_configuration=f"{specs.get('size_gb', '')} GB gp2 volume",
                recommended_configuration=f"{specs.get('size_gb', '')} GB gp3 volume (3,000 baseline IOPS, 20% lower cost)",
                estimated_monthly_savings=waste,
                estimated_annual_savings=waste * Decimal("12"),
                confidence_score=Decimal("98.00"),
                risk_level="NONE",
                reasoning="gp3 provides superior or equal baseline throughput at a 20% published price reduction with zero downtime in-place migration.",
                assumptions_json=assumptions,
                evidence_json={"volume_type": "gp2", "target_type": "gp3"},
            )

            opp = OpportunityCandidate(
                account_id=resource["account_id"],
                account_name=account_name,
                resource_id=resource["id"],
                resource_name=resource.get("name"),
                resource_native_id=resource.get("native_id"),
                category=cls.category,
                waste_type=cls.waste_type,
                severity=Severity.MEDIUM,
                estimated_waste_monthly=waste,
                evidence_json={"volume_type": "gp2", "assumptions": assumptions},
                confidence_score=Decimal("98.00"),
                recommendations=[rec],
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                opp,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.waste_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )


class UnassociatedEIPRule:
    """Conditional Rule: Detects unallocated IPv4 Elastic IP addresses."""
    rule_id = "WASTE-RULE-UNASSOCIATED-EIP"
    waste_type = WasteType.UNASSOCIATED_EIP
    category = "NETWORKING"
    contract = EvidenceContract(
        rule_name="UnassociatedEIPRule",
        required_fields=["idle_duration_days"],
        min_sample_size=1,
        telemetry_source="operational",
    )

    @classmethod
    def evaluate(
        cls,
        resource: Dict[str, Any],
        monthly_cost: Decimal,
        account_name: str,
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[OpportunityCandidate]]:
        specs = resource.get("specs_json") or {}
        is_satisfied, reason = cls.contract.check(specs)
        if not is_satisfied:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=reason,
                    findings_count=0,
                ),
                None,
            )

        idle_days = int(specs.get("idle_duration_days", 0))
        is_unattached = str(specs.get("association_status", "UNATTACHED")).upper() in ("UNATTACHED", "UNALLOCATED")

        if is_unattached and idle_days >= UNASSOCIATED_EIP_MIN_DAYS:
            waste = monthly_cost.quantize(Decimal("0.0001"))
            rec = RecommendationCandidate(
                title="Release Unassociated Static Elastic IP Address",
                category="NETWORKING",
                current_configuration="Unallocated Elastic IP address",
                recommended_configuration="Release IP address to pool",
                estimated_monthly_savings=waste,
                estimated_annual_savings=waste * Decimal("12"),
                confidence_score=Decimal("99.00"),
                risk_level="NONE",
                reasoning=f"Elastic IP has remained unassociated for {idle_days} days incurring idle IPv4 reservation charges.",
                assumptions_json={"waste_ratio": "1.00"},
                evidence_json={"idle_duration_days": idle_days},
            )

            opp = OpportunityCandidate(
                account_id=resource["account_id"],
                account_name=account_name,
                resource_id=resource["id"],
                resource_name=resource.get("name"),
                resource_native_id=resource.get("native_id"),
                category=cls.category,
                waste_type=cls.waste_type,
                severity=Severity.LOW,
                estimated_waste_monthly=waste,
                evidence_json={"idle_duration_days": idle_days},
                confidence_score=Decimal("99.00"),
                recommendations=[rec],
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                opp,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.waste_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )


class UnmanagedObjectVersionsRule:
    """Conditional Rule: Detects S3 buckets accumulating untiered non-current versions without lifecycle rules."""
    rule_id = "WASTE-RULE-UNMANAGED-OBJECT-VERSIONS"
    waste_type = WasteType.UNMANAGED_OBJECT_VERSIONS
    category = "STORAGE"
    contract = EvidenceContract(
        rule_name="UnmanagedObjectVersionsRule",
        required_fields=["non_current_versions_gb", "lifecycle_rules_found"],
        min_sample_size=1,
        telemetry_source="operational",
    )

    @classmethod
    def evaluate(
        cls,
        resource: Dict[str, Any],
        monthly_cost: Decimal,
        account_name: str,
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[OpportunityCandidate]]:
        specs = resource.get("specs_json") or {}
        is_satisfied, reason = cls.contract.check(specs)
        if not is_satisfied:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=reason,
                    findings_count=0,
                ),
                None,
            )

        versions_gb = int(specs.get("non_current_versions_gb", 0))
        lifecycle_rules = int(specs.get("lifecycle_rules_found", 0))

        if versions_gb >= 1000 and lifecycle_rules == 0:
            waste = monthly_cost.quantize(Decimal("0.0001"))
            rec = RecommendationCandidate(
                title="Configure S3 Lifecycle Expiration & Cold Tiering",
                category="STORAGE",
                current_configuration=f"Retaining {versions_gb} GB non-current versions in S3 Standard",
                recommended_configuration="Expire non-current versions after 14 days; transition aged objects to Glacier Instant Retrieval",
                estimated_monthly_savings=waste,
                estimated_annual_savings=waste * Decimal("12"),
                confidence_score=Decimal("89.00"),
                risk_level="LOW",
                reasoning=f"Bucket contains {versions_gb} GB of superseded versions with zero lifecycle expiration policies configured.",
                assumptions_json={"action": "EXPIRE_NON_CURRENT", "transition": "GLACIER_IR"},
                evidence_json={"non_current_versions_gb": versions_gb, "lifecycle_rules": lifecycle_rules},
            )

            opp = OpportunityCandidate(
                account_id=resource["account_id"],
                account_name=account_name,
                resource_id=resource["id"],
                resource_name=resource.get("name"),
                resource_native_id=resource.get("native_id"),
                category=cls.category,
                waste_type=cls.waste_type,
                severity=Severity.HIGH,
                estimated_waste_monthly=waste,
                evidence_json={
                    "non_current_versions_gb": versions_gb,
                    "lifecycle_rules_found": lifecycle_rules,
                },
                confidence_score=Decimal("89.00"),
                recommendations=[rec],
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.waste_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                opp,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.waste_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )
