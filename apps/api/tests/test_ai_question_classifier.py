"""
NEXORA ATLAS - Phase 9 Milestone 2: Question Classifier Test Suite
Verifies deterministic routing of natural language inquiries into canonical QuestionCategories.
Confirms classifier acts as a router, not an intelligence or security engine.
"""

import pytest
from app.ai.types import QuestionCategory, ScopeType
from app.ai.questions.classifier import (
    DeterministicQuestionClassifier,
    default_classifier,
    classify_query,
    QueryIntent,
)


def test_classify_spend_overview_questions():
    """Test 1: SPEND_OVERVIEW classification."""
    queries = [
        "How much did we spend this month?",
        "Total spend across all accounts",
        "What is our current cloud spend?",
        "Monthly run rate overview",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.SPEND_OVERVIEW


def test_classify_spend_change_questions():
    """Test 2: SPEND_CHANGE classification."""
    queries = [
        "Why did spend increase?",
        "Why did cloud cost spike last month?",
        "What caused the spend surge?",
        "Difference between August and September spend",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.SPEND_CHANGE


def test_classify_cost_driver_questions():
    """Test 3: COST_DRIVER classification."""
    queries = [
        "Which resources are driving the increase?",
        "What are the top drivers of spend?",
        "Which service drove the cost growth?",
        "Cost breakdown by driver",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.COST_DRIVER


def test_classify_resource_questions():
    """Test 4: RESOURCE classification."""
    queries = [
        "Show me expensive resources",
        "What is this resource doing?",
        "Resource configuration for i-0123456789abcdef0",
        "Tell me about instance specs",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.RESOURCE


def test_classify_optimization_questions():
    """Test 5: OPTIMIZATION classification."""
    queries = [
        "What can we optimize?",
        "How can we reduce cloud cost?",
        "Can we downsize this instance?",
        "Show waste and idle resources",
        "Are there rightsizing recommendations?",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.OPTIMIZATION


def test_classify_scenario_questions():
    """Test 6: SCENARIO classification."""
    queries = [
        "What happens if we resize this?",
        "What if we migrate to Graviton?",
        "Simulate the savings from rightsizing",
        "Model future state under aggressive scenario",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.SCENARIO


def test_classify_unsupported_external_questions():
    """Test 7: UNSUPPORTED external domain questions."""
    queries = [
        "What is the weather tomorrow in Mumbai?",
        "Who won the cricket match yesterday?",
        "Give me a pasta recipe",
        "What is the bitcoin price today?",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.UNSUPPORTED


def test_classify_telemetry_questions():
    """TELEMETRY classification for operational performance queries."""
    queries = [
        "What is CPU utilization for this instance?",
        "Show memory utilization metrics",
        "What is the IOPS and disk write activity?",
        "Show CloudWatch telemetry",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.TELEMETRY


def test_classify_anomaly_questions():
    """ANOMALY classification for unexpected cost deviations."""
    queries = [
        "Show me recent anomalies",
        "Was there any unusual spend spike?",
        "Are there abnormal charges this week?",
        "List all cost deviations",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.ANOMALY


def test_classify_forecast_questions():
    """FORECAST classification for status-quo run rate projections."""
    queries = [
        "What will spending look like next month?",
        "Projected spend forecast",
        "What is our future spend trajectory?",
    ]
    for q in queries:
        assert default_classifier.classify_question(q) == QuestionCategory.FORECAST


def test_classify_account_and_service_questions():
    """ACCOUNT and SERVICE specific classification."""
    assert default_classifier.classify_question("How much did production account spend?") == QuestionCategory.ACCOUNT
    assert default_classifier.classify_question("What happened to EC2 spend?") == QuestionCategory.SERVICE


def test_classifier_does_not_manufacture_confidence_scores():
    """
    CRITICAL: Classifier must not output AI-generated confidence scores.
    """
    intent = default_classifier.classify_intent("Why did spend increase?")
    assert isinstance(intent, QueryIntent)
    assert intent.category == QuestionCategory.SPEND_CHANGE
    assert not hasattr(intent, "ai_confidence")
