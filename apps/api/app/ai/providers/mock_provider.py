"""
NEXORA ATLAS - Mock AI Provider (Phase 9 Milestone 3)
100% offline, deterministic provider synthesizing structured AICandidateAnswers directly
from BoundedContext evidence items.
Guarantees zero external network dependencies for local development, CI, and Golden Scenarios.
Strictly prohibits AI-generated confidence scores.
"""

import time
from typing import List, Dict, Any, Optional
from decimal import Decimal

from app.ai.types import EpistemicClass, AIResponseStatus
from app.ai.models import (
    EvidenceItem,
    EvidencePackage,
    AIAnswer,
    AIConclusion,
    NumericClaim,
    AIResponse,
)
from app.ai.constants import INPUT_COST_PER_1K_TOKENS, OUTPUT_COST_PER_1K_TOKENS
from app.ai.providers.models import (
    AIProviderRequest,
    AIProviderResult,
    AICandidateAnswer,
    AICandidateConclusion,
    AICandidateCitation,
    AICandidateNumericClaim,
)


class MockAIProvider:
    """
    Offline deterministic provider generating structured candidate explanations from evidence.
    Implements Golden Scenarios A through H deterministically.
    """

    def __init__(self, simulate_latency_ms: int = 15):
        self.simulate_latency_ms = simulate_latency_ms

    async def generate_candidate(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResult:
        """
        Primary M3 method: Generates an untrusted AICandidateAnswer envelope
        from the M2 BoundedContext.
        """
        start_time = time.monotonic()
        q_lower = request.question.lower()

        # Extract evidence items from bounded_context
        evidence_items: List[EvidenceItem] = []
        limitations: List[str] = []
        freshness_summary = "Authoritative Atlas data."

        if request.bounded_context:
            evidence_items = request.bounded_context.evidence_items
            limitations = list(request.bounded_context.limitations)
            freshness_summary = f"Data freshness status: {request.bounded_context.freshness_status.value}"

        telemetry_items = [
            i for i in evidence_items
            if i.type in ("METRIC_P95", "TELEMETRY") or "telemetry" in i.source.lower() or "cloudwatch" in i.source.lower()
        ]
        recommendation_items = [i for i in evidence_items if i.type == "RECOMMENDATION"]
        scenario_items = [i for i in evidence_items if i.type == "SCENARIO"]
        observation_items = [
            i for i in evidence_items
            if i.type not in ("RECOMMENDATION", "SCENARIO")
        ]

        conclusions: List[AICandidateConclusion] = []
        next_steps: List[str] = []
        citations: List[AICandidateCitation] = []
        epistemic_notes: List[str] = []
        summary = ""
        answer = ""

        # SCENARIO H: Numerical Hallucination Simulation
        if "hallucination" in q_lower or "fake numbers" in q_lower or "wrong savings" in q_lower:
            # Emits ₹920,000 against evidence containing ₹460,000
            claim_val = Decimal("920000.00")
            fake_ev_id = "ev-fake-999"
            if evidence_items:
                fake_ev_id = evidence_items[0].id

            conclusions.append(
                AICandidateConclusion(
                    statement="Monthly infrastructure optimization savings can reach ₹9,20,000.00 per month.",
                    epistemic_class=EpistemicClass.INFERRED,
                    evidence_ids=[fake_ev_id],
                    numeric_claims=[
                        AICandidateNumericClaim(
                            value=claim_val,
                            unit="INR",
                            evidence_id=fake_ev_id,
                        )
                    ],
                )
            )
            summary = "Simulated candidate with inflated numerical claim (testing M4 rejection gate)."
            answer = "The infrastructure optimization decision promises ₹9,20,000.00 in monthly cost reduction across all accounts."
            epistemic_notes.append("Hallucinated numeric claim candidate generated for M4 verification testing.")

        # SCENARIO E: Multi-AZ Database
        elif "database" in q_lower or "multi-az" in q_lower or "rds" in q_lower:
            db_cost = Decimal("120000.00")
            db_ev_id = "ev-db-rds-1"
            for item in observation_items:
                if "rds" in item.statement.lower() or "database" in item.statement.lower():
                    db_cost = item.value or db_cost
                    db_ev_id = item.id
                    break

            conclusions.append(
                AICandidateConclusion(
                    statement=f"Production Multi-AZ RDS instance observed with low active query traffic, costing ₹{db_cost:,.2f}/month.",
                    epistemic_class=EpistemicClass.OBSERVED,
                    evidence_ids=[db_ev_id],
                    numeric_claims=[
                        AICandidateNumericClaim(value=db_cost, unit="INR", evidence_id=db_ev_id)
                    ],
                )
            )
            conclusions.append(
                AICandidateConclusion(
                    statement="The database provides high availability failover and production reliability; termination is contraindicated and termination is not recommended.",
                    epistemic_class=EpistemicClass.INFERRED,
                    evidence_ids=[db_ev_id],
                    numeric_claims=[],
                )
            )
            summary = "Production database is Multi-AZ with baseline standby requirements."
            answer = (
                f"The database instance incurs ₹{db_cost:,.2f}/month. Although current transaction volume is low, "
                "the Multi-AZ configuration satisfies high-availability and business continuity SLAs. "
                "Atlas does not recommend destructive actions or termination of active production clusters."
            )
            epistemic_notes.append("Destructive action prohibition: Multi-AZ cluster cannot be recommended for deletion.")

        # SCENARIO B: Insufficient Telemetry
        elif (
            "downsize" in q_lower or "reduce" in q_lower or "cpu" in q_lower or "utilization" in q_lower
        ) and len(telemetry_items) == 0:
            conclusions.append(
                AICandidateConclusion(
                    statement="Operational telemetry for this resource is currently unavailable. No CPU or memory utilization can be verified.",
                    epistemic_class=EpistemicClass.NOT_AVAILABLE,
                    evidence_ids=[],
                    numeric_claims=[],
                )
            )
            limitations.append("CloudWatch metrics have not been ingested or synchronized for this resource.")
            next_steps.append("Trigger an on-demand CloudWatch synchronization job to collect operational telemetry.")
            summary = "Insufficient operational telemetry to assess resource utilization."
            answer = (
                "Atlas has not observed operational telemetry for this resource. "
                "Under Atlas epistemic rules, utilization metrics cannot be inferred, modeled, or assumed without direct CloudWatch observations. "
                "Downsizing without telemetry data carries high operational risk."
            )
            epistemic_notes.append("Utilization state classified as NOT_AVAILABLE per strict evidence verification rules.")

        # SCENARIO D: High Memory Constraint (Low CPU, High Memory)
        elif self._has_high_memory_constraint(telemetry_items):
            mem_item, cpu_item = self._get_mem_and_cpu_items(telemetry_items)
            cpu_val = cpu_item.value if cpu_item and cpu_item.value else Decimal("12.5")
            mem_val = mem_item.value if mem_item and mem_item.value else Decimal("88.0")

            conclusions.append(
                AICandidateConclusion(
                    statement=f"Average CPU utilization is low ({cpu_val}%), but peak memory utilization is elevated at {mem_val}%.",
                    epistemic_class=EpistemicClass.DERIVED,
                    evidence_ids=[cpu_item.id, mem_item.id] if cpu_item and mem_item else [],
                    numeric_claims=[
                        AICandidateNumericClaim(value=cpu_val, unit="%", evidence_id=cpu_item.id if cpu_item else "cpu-1"),
                        AICandidateNumericClaim(value=mem_val, unit="%", evidence_id=mem_item.id if mem_item else "mem-1"),
                    ],
                )
            )
            conclusions.append(
                AICandidateConclusion(
                    statement="Downsizing this instance to a smaller standard instance family would risk out-of-memory (OOM) failures.",
                    epistemic_class=EpistemicClass.INFERRED,
                    evidence_ids=[mem_item.id] if mem_item else [],
                    numeric_claims=[],
                )
            )
            summary = "Compute downsizing not recommended due to high memory footprint."
            answer = (
                f"While CPU utilization remains low at {cpu_val}%, memory usage peaks at {mem_val}%. "
                "A standard CPU-focused rightsizing would cause severe memory exhaustion. "
                "Consider transitioning to a memory-optimized instance tier instead of a generic downsize."
            )
            epistemic_notes.append("Epistemic constraint: CPU underutilization does not justify compute downsizing when memory is constrained.")

        # SCENARIO F: Scenario Projection
        elif "scenario" in q_lower or "what if" in q_lower or "migrate" in q_lower or "graviton" in q_lower:
            savings_val = Decimal("35000.00")
            scen_id = "scen-golden-01"
            if scenario_items:
                savings_val = scenario_items[0].value or savings_val
                scen_id = scenario_items[0].id

            conclusions.append(
                AICandidateConclusion(
                    statement=f"Simulated scenario has projected estimated monthly savings of ₹{savings_val:,.2f}.",
                    epistemic_class=EpistemicClass.PROJECTED,
                    evidence_ids=[scen_id],
                    numeric_claims=[
                        AICandidateNumericClaim(value=savings_val, unit="INR", evidence_id=scen_id)
                    ],
                )
            )
            summary = "Hypothetical scenario projection."
            answer = (
                f"Under the Graviton modernization scenario, the projected monthly savings are ₹{savings_val:,.2f}. "
                "Note: These are projected hypothetical savings under simulation assumptions, NOT actual historical savings."
            )
            epistemic_notes.append("PROJECTED epistemic class strictly preserved; not presented as observed facts.")

        # SCENARIO C: Rightsizing Opportunity
        elif ("rightsize" in q_lower or "recommend" in q_lower) and len(recommendation_items) > 0:
            rec = recommendation_items[0]
            rec_savings = rec.value or Decimal("14500.00")
            conclusions.append(
                AICandidateConclusion(
                    statement=f"Optimization recommendation '{rec.statement}' identified with estimated monthly savings of ₹{rec_savings:,.2f}.",
                    epistemic_class=EpistemicClass.INFERRED,
                    evidence_ids=[rec.id],
                    numeric_claims=[
                        AICandidateNumericClaim(value=rec_savings, unit="INR", evidence_id=rec.id)
                    ],
                )
            )
            limitations.append("Workload peak validation and headroom checks are required before downsizing.")
            summary = "Rightsizing opportunity available based on observed utilization."
            answer = (
                f"Atlas identifies a rightsizing opportunity with estimated savings of ₹{rec_savings:,.2f}/month. "
                "Hardware telemetry indicates the instance can safely step down one instance size."
            )
            epistemic_notes.append("Optimization savings classified as INFERRED based on analytical heuristics.")

        # SCENARIO A: Spend Increase / Overview (Default fallback)
        else:
            total_spend = Decimal("161000.00")
            top_driver_name = "Amazon Elastic Kubernetes Service"
            top_driver_cost = Decimal("82000.00")
            driver_ev_id = "ev-cost-eks"
            total_ev_id = "ev-total-spend"

            if observation_items:
                total_ev_id = observation_items[0].id
                if observation_items[0].value:
                    total_spend = observation_items[0].value

                if len(observation_items) > 1 and observation_items[1].value:
                    top_driver_cost = observation_items[1].value
                    top_driver_name = observation_items[1].statement.split(":")[0] if ":" in observation_items[1].statement else "EC2"
                    driver_ev_id = observation_items[1].id

            conclusions.append(
                AICandidateConclusion(
                    statement=f"Cloud spend increased, driven primarily by {top_driver_name} at ₹{top_driver_cost:,.2f}.",
                    epistemic_class=EpistemicClass.OBSERVED,
                    evidence_ids=[driver_ev_id],
                    numeric_claims=[
                        AICandidateNumericClaim(value=top_driver_cost, unit="INR", evidence_id=driver_ev_id)
                    ],
                )
            )
            conclusions.append(
                AICandidateConclusion(
                    statement=f"Total observed expenditure for the period is ₹{total_spend:,.2f}.",
                    epistemic_class=EpistemicClass.DERIVED,
                    evidence_ids=[total_ev_id],
                    numeric_claims=[
                        AICandidateNumericClaim(value=total_spend, unit="INR", evidence_id=total_ev_id)
                    ],
                )
            )
            summary = f"Spend increase driven primarily by {top_driver_name}."
            answer = (
                f"Cloud infrastructure expenditure rose to ₹{total_spend:,.2f}. "
                f"The primary cost driver was {top_driver_name}, contributing ₹{top_driver_cost:,.2f}. "
                "Additional spend growth was observed in container scaling and storage activity."
            )
            epistemic_notes.append("Spend delta derived from authoritative billing records.")

        candidate = AICandidateAnswer(
            summary=summary,
            answer=answer,
            conclusions=conclusions,
            limitations=limitations,
            recommended_next_steps=next_steps,
            cited_entities=citations,
            epistemic_notes=epistemic_notes,
            freshness_note=freshness_summary,
        )

        input_toks = len(request.user_prompt) // 4 + 100
        output_toks = len(answer) // 4 + 80
        total_toks = input_toks + output_toks

        cost = (
            (Decimal(input_toks) / Decimal(1000) * INPUT_COST_PER_1K_TOKENS)
            + (Decimal(output_toks) / Decimal(1000) * OUTPUT_COST_PER_1K_TOKENS)
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000) or self.simulate_latency_ms

        return AIProviderResult(
            status=AIResponseStatus.COMPLETED,
            provider="mock",
            model="atlas-mock-engine-v1",
            candidate_answer=candidate,
            raw_response_text=candidate.model_dump_json(),
            raw_response_metadata={"mock": True, "fixture": "deterministic"},
            input_tokens=input_toks,
            output_tokens=output_toks,
            total_tokens=total_toks,
            estimated_cost_usd=cost,
            latency_ms=elapsed_ms,
            request_id=request.request_id,
            evidence_hash=request.evidence_hash,
        )

    async def generate_explanation(
        self,
        question: str,
        evidence_package: EvidencePackage,
        session_history: Optional[List[Dict[str, str]]] = None,
    ) -> AIResponse:
        """
        Dual-compatibility adapter conforming to existing AIProviderContract.
        """
        from app.ai.prompts.builder import PromptBuilder

        request = PromptBuilder.build_request(
            question=question,
            evidence_package=evidence_package,
            session_history=session_history,
        )
        res = await self.generate_candidate(request)

        ans = None
        if res.candidate_answer:
            conclusions = [
                AIConclusion(
                    statement=c.statement,
                    epistemic_class=c.epistemic_class,
                    evidence_ids=c.evidence_ids,
                    numeric_claims=[
                        NumericClaim(value=nc.value, unit=nc.unit, evidence_id=nc.evidence_id)
                        for nc in c.numeric_claims
                    ],
                )
                for c in res.candidate_answer.conclusions
            ]
            ans = AIAnswer(
                summary=res.candidate_answer.summary,
                answer=res.candidate_answer.answer,
                conclusions=conclusions,
                limitations=res.candidate_answer.limitations,
                recommended_next_steps=res.candidate_answer.recommended_next_steps,
                cited_entities=[],
                epistemic_notes=res.candidate_answer.epistemic_notes,
                freshness_note=res.candidate_answer.freshness_note,
            )

        return AIResponse(
            status=res.status,
            answer=ans,
            input_tokens=res.input_tokens,
            output_tokens=res.output_tokens,
            total_tokens=res.total_tokens,
            latency_ms=res.latency_ms,
            estimated_cost_usd=res.estimated_cost_usd,
        )

    def _has_high_memory_constraint(self, items: List[EvidenceItem]) -> bool:
        for t in items:
            if "memory" in t.id.lower() or "memory" in t.statement.lower():
                if t.value and t.value > Decimal("65.0"):
                    return True
        return False

    def _get_mem_and_cpu_items(self, items: List[EvidenceItem]):
        mem_item = None
        cpu_item = None
        for t in items:
            if "memory" in t.id.lower() or "memory" in t.statement.lower():
                mem_item = t
            elif "cpu" in t.id.lower() or "cpu" in t.statement.lower():
                cpu_item = t
        return mem_item, cpu_item
