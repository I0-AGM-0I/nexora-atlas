"""
NEXORA ATLAS - Deterministic Question Classifier (Phase 9)
Classifies natural-language inquiries into one of the 13 canonical QuestionCategories.

CRITICAL ARCHITECTURAL PHILOSOPHY:
  The classifier is a ROUTER, not an intelligence engine and NOT a security boundary.
  It determines which evidence retrieval strategy should run.
  It does NOT determine what the answer is, and it CANNOT grant or expand tenant authorization.
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field

from app.ai.types import QuestionCategory, ScopeType
from app.ai.contracts import QueryClassifierContract


class QueryIntent(BaseModel):
    """Routing metadata resulting from question classification."""
    category: QuestionCategory
    detected_services: List[str] = Field(default_factory=list)
    detected_metrics: List[str] = Field(default_factory=list)
    primary_intent: str = ""


# Lexical patterns for deterministic intent routing
CATEGORY_PATTERNS = [
    # 1. SCENARIO (hypothetical future-state simulation, before OPTIMIZATION)
    (
        QuestionCategory.SCENARIO,
        [
            r"what if",
            r"what happens if",
            r"what would happen if",
            r"scenario",
            r"simulate",
            r"model.*(savings|future|scenario)",
            r"impact of migrating",
            r"future state",
        ]
    ),
    # 2. COST_DRIVER (attribution and contributor decomposition, before SPEND_CHANGE)
    (
        QuestionCategory.COST_DRIVER,
        [
            r"what (are|is) the .*(driver|drivers|contributors?)",
            r"which (service|resource|account).*drove",
            r"which resources are driving",
            r"who is driving the (cost|spend)",
            r"driver(s)? of (cost|spend)",
            r"cost breakdown by driver",
            r"contributed to (spend|cost)",
            r"top drivers",
        ]
    ),
    # 3. ANOMALY (statistical deviation and anomaly events, before SPEND_CHANGE)
    (
        QuestionCategory.ANOMALY,
        [
            r"anomal(y|ies)",
            r"unusual.*(spend|activity|spike|cost)",
            r"abnormal",
            r"unexpected charge",
            r"outlier",
            r"deviation",
        ]
    ),
    # 4. SPEND_CHANGE (explicit delta/increase/decrease inquiry)
    (
        QuestionCategory.SPEND_CHANGE,
        [
            r"why did.*(spend|cost|spending).*(increase|decrease|change|spike|rise|drop|jump|surge|grow)",
            r"why did.*(increase|decrease|spike|surge|jump|drop)",
            r"what caused the.*(increase|decrease|spike|change|rise|surge|jump)",
            r"(spend|cost).*(increase|decrease|growth|jump|surge|drop|spike)",
            r"diff(erence)? between",
            r"compare.*(spend|cost|months)",
        ]
    ),
    # 5. OPTIMIZATION (rightsizing, waste, savings opportunities)
    (
        QuestionCategory.OPTIMIZATION,
        [
            r"what can we optimize",
            r"how can (we|i) (save|cut|reduce|optimize)",
            r"can we (reduce|downsize|shrink|optimize)",
            r"optimization(s)?",
            r"recommendation(s)?",
            r"rightsizing",
            r"graviton",
            r"idle (resource|database|instance)",
            r"waste",
            r"save money",
            r"cost reduction",
        ]
    ),
    # 6. TELEMETRY (operational performance and CloudWatch metrics)
    (
        QuestionCategory.TELEMETRY,
        [
            r"what is cpu( utilization)?",
            r"cpu( utilization)?",
            r"memory( utilization)?",
            r"iops",
            r"telemetry",
            r"cloudwatch",
            r"connections",
            r"utilization metrics",
            r"network (in|out|bytes)",
            r"disk (read|write|bytes)",
        ]
    ),
    # 7. FORECAST (organic spend projection under status quo)
    (
        QuestionCategory.FORECAST,
        [
            r"what will spending look like",
            r"forecast",
            r"next month",
            r"projected spend",
            r"future (cost|spend)",
            r"trajectory",
            r"projected run rate",
        ]
    ),
    # 8. RESOURCE (individual resource queries)
    (
        QuestionCategory.RESOURCE,
        [
            r"show me expensive resources",
            r"what is this resource doing",
            r"resource config(uration)?",
            r"expensive resource(s)?",
            r"resource details",
            r"i-[a-z0-9]+",
            r"vol-[a-z0-9]+",
            r"instance type",
            r"instance spec",
        ]
    ),
    # 9. ACCOUNT (cloud account spend and scope)
    (
        QuestionCategory.ACCOUNT,
        [
            r"account spend",
            r"account breakdown",
            r"how much did.*account spend",
            r"production account",
            r"development account",
            r"staging account",
            r"12-digit",
        ]
    ),
    # 10. SERVICE (cloud service specific inquiries)
    (
        QuestionCategory.SERVICE,
        [
            r"what happened to (ec2|eks|rds|s3|dynamodb|lambda)",
            r"(ec2|eks|rds|s3|dynamodb|lambda) spend",
            r"(ec2|eks|rds|s3|dynamodb|lambda) cost",
            r"service cost",
        ]
    ),
    # 11. SPEND_OVERVIEW (general baseline and aggregate totals)
    (
        QuestionCategory.SPEND_OVERVIEW,
        [
            r"how much did we spend",
            r"how much.*spend",
            r"total spend",
            r"total cloud spend",
            r"current.*spend",
            r"what is our.*spend",
            r"spend overview",
            r"monthly run rate",
            r"run rate overview",
            r"spend summary",
        ]
    ),
]

SERVICE_SYNONYMS = {
    "eks": "Amazon Elastic Kubernetes Service",
    "kubernetes": "Amazon Elastic Kubernetes Service",
    "ec2": "Amazon Elastic Compute Cloud - Compute",
    "rds": "Amazon Relational Database Service",
    "s3": "Amazon Simple Storage Service",
    "dynamodb": "Amazon DynamoDB",
    "lambda": "AWS Lambda",
    "ebs": "EC2 - Other",
}

METRIC_SYNONYMS = {
    "cpu": "CPUUtilization",
    "memory": "MemoryUtilization",
    "iops": "EBSReadBytes",
    "disk": "EBSWriteBytes",
    "connections": "DatabaseConnections",
}

UNSUPPORTED_PATTERNS = [
    r"weather",
    r"cricket",
    r"football",
    r"recipe",
    r"movie",
    r"joke",
    r"stock market",
    r"bitcoin",
    r"crypto price",
    r"translate",
]

GENERAL_ATLAS_PATTERNS = [
    r"what is atlas",
    r"how does atlas work",
    r"what can you do",
    r"atlas capabilities",
    r"help me with atlas",
]


class DeterministicQuestionClassifier:
    """
    Implements QueryClassifierContract.
    Deterministically routes natural language questions to QuestionCategory.
    """

    def classify_question(self, question: str) -> QuestionCategory:
        """Classifies a user query into one of the 13 canonical QuestionCategories."""
        intent = self.classify_intent(question)
        return intent.category

    def classify_intent(
        self,
        question: str,
        scope_type: ScopeType = ScopeType.DASHBOARD,
        scope_id: Optional[str] = None,
    ) -> QueryIntent:
        """Full deterministic classification including entity recognition."""
        clean_q = question.lower().strip()

        # Check for unsupported external domain questions
        if any(re.search(pat, clean_q) for pat in UNSUPPORTED_PATTERNS):
            return QueryIntent(
                category=QuestionCategory.UNSUPPORTED,
                primary_intent="Unsupported external query outside Atlas domain",
            )

        # Check for general Atlas product questions
        if any(re.search(pat, clean_q) for pat in GENERAL_ATLAS_PATTERNS):
            return QueryIntent(
                category=QuestionCategory.GENERAL_ATLAS,
                primary_intent="General Atlas platform guidance",
            )

        # If scope is explicitly pinned to a domain entity, respect that context unless query asks for scenario
        if scope_type == ScopeType.RESOURCE and not any(k in clean_q for k in ["scenario", "what if", "forecast"]):
            if any(k in clean_q for k in ["cpu", "memory", "utilization", "telemetry", "metric"]):
                category = QuestionCategory.TELEMETRY
            elif any(k in clean_q for k in ["save", "cut", "reduce", "optimize", "rightsize"]):
                category = QuestionCategory.OPTIMIZATION
            else:
                category = QuestionCategory.RESOURCE
        elif scope_type == ScopeType.RECOMMENDATION:
            category = QuestionCategory.OPTIMIZATION
        elif scope_type == ScopeType.SCENARIO:
            category = QuestionCategory.SCENARIO
        else:
            # Pattern matching against canonical categories
            matched_cat = None
            for cat, patterns in CATEGORY_PATTERNS:
                if any(re.search(pat, clean_q) for pat in patterns):
                    matched_cat = cat
                    break
            
            category = matched_cat if matched_cat is not None else QuestionCategory.GENERAL_ATLAS

        # Detect service mentions
        detected_services = []
        for syn, svc_name in SERVICE_SYNONYMS.items():
            if syn in clean_q and svc_name not in detected_services:
                detected_services.append(svc_name)

        # Detect metric mentions
        detected_metrics = []
        for syn, metric_name in METRIC_SYNONYMS.items():
            if syn in clean_q and metric_name not in detected_metrics:
                detected_metrics.append(metric_name)

        return QueryIntent(
            category=category,
            detected_services=detected_services,
            detected_metrics=detected_metrics,
            primary_intent=f"Query {category.value} for scope {scope_type.value}",
        )


# Global default instance
default_classifier = DeterministicQuestionClassifier()


def classify_query(
    question: str,
    scope_type: ScopeType = ScopeType.DASHBOARD,
    scope_id: Optional[str] = None,
) -> QueryIntent:
    """Convenience functional wrapper matching existing router interface."""
    return default_classifier.classify_intent(question, scope_type, scope_id)
