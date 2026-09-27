"""
NEXORA ATLAS - Query Router & Intent Classifier (Phase 9)
Deterministically classifies user prompts into question categories
and extracts entity references for evidence gathering.
NOTE: This router does NOT grant permissions; scope authorization happens prior.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.ai.types import QuestionCategory, ScopeType


class QueryIntent(BaseModel):
    category: QuestionCategory
    confidence: float = 1.0  # Routing classification confidence
    detected_services: List[str] = Field(default_factory=list)
    detected_metrics: List[str] = Field(default_factory=list)
    primary_intent: str = ""


# Keywords for question classification
CATEGORY_PATTERNS = [
    (
        QuestionCategory.SPEND_CHANGE,
        [
            r"why did (spend|cost) (increase|decrease|change|spike|rise|drop|jump)",
            r"what caused the (increase|decrease|spike|change|rise)",
            r"(spend|cost) (increase|decrease|change|growth|delta)",
            r"diff(erence)? between.*(month|period|week)",
        ]
    ),
    (
        QuestionCategory.COST_DRIVER,
        [
            r"what (are|is) the (biggest|main|primary|top) (driver|drivers|contributors?)",
            r"which service drove",
            r"who is driving the cost",
            r"driver(s)? of (cost|spend)",
        ]
    ),
    (
        QuestionCategory.ANOMALY,
        [
            r"anomal(y|ies)",
            r"unusual (spend|activity|spike)",
            r"abnormal",
            r"unexpected charge",
        ]
    ),
    (
        QuestionCategory.OPTIMIZATION,
        [
            r"how can (we|i) (save|cut|reduce|optimize)",
            r"optimization(s)?",
            r"recommendation(s)?",
            r"rightsizing",
            r"graviton",
            r"idle (resource|database|instance)",
            r"waste",
        ]
    ),
    (
        QuestionCategory.TELEMETRY,
        [
            r"cpu( utilization)?",
            r"memory( utilization)?",
            r"iops",
            r"telemetry",
            r"cloudwatch",
            r"connections",
            r"utilization metrics",
        ]
    ),
    (
        QuestionCategory.SCENARIO,
        [
            r"scenario",
            r"what if",
            r"simulate",
            r"model savings",
            r"impact of migrating",
        ]
    ),
    (
        QuestionCategory.FORECAST,
        [
            r"forecast",
            r"next month",
            r"projected spend",
            r"future (cost|spend)",
            r"trajectory",
        ]
    ),
    (
        QuestionCategory.RESOURCE,
        [
            r"resource",
            r"instance",
            r"i-[a-z0-9]+",
            r"vol-[a-z0-9]+",
            r"database",
            r"cluster",
        ]
    ),
    (
        QuestionCategory.SPEND_OVERVIEW,
        [
            r"total spend",
            r"how much did we spend",
            r"current spend",
            r"overview",
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


def classify_query(
    question: str,
    scope_type: ScopeType = ScopeType.DASHBOARD,
    scope_id: Optional[str] = None,
) -> QueryIntent:
    """
    Deterministically determines the question category and extracts entities.
    """
    clean_q = question.lower().strip()

    # If the scope is already specifically pinned to a resource or scenario, respect that context
    if scope_type == ScopeType.RESOURCE and not any(k in clean_q for k in ["scenario", "forecast"]):
        category = QuestionCategory.RESOURCE
    elif scope_type == ScopeType.RECOMMENDATION:
        category = QuestionCategory.OPTIMIZATION
    elif scope_type == ScopeType.SCENARIO:
        category = QuestionCategory.SCENARIO
    else:
        matched_cat = QuestionCategory.SPEND_OVERVIEW
        for cat, patterns in CATEGORY_PATTERNS:
            if any(re.search(pat, clean_q) for pat in patterns):
                matched_cat = cat
                break
        category = matched_cat

    # Detect service mentions
    detected_services = []
    for syn, svc_name in SERVICE_SYNONYMS.items():
        if syn in clean_q:
            if svc_name not in detected_services:
                detected_services.append(svc_name)

    # Detect metric mentions
    detected_metrics = []
    for syn, metric_name in METRIC_SYNONYMS.items():
        if syn in clean_q:
            if metric_name not in detected_metrics:
                detected_metrics.append(metric_name)

    return QueryIntent(
        category=category,
        confidence=1.0,
        detected_services=detected_services,
        detected_metrics=detected_metrics,
        primary_intent=f"Query {category.value} for scope {scope_type.value}"
    )
