"""
NEXORA ATLAS - Phase 9 Milestone 3: OpenAI Provider Test Suite
Mocks external network calls via httpx to test OpenAIProvider in isolation.
Validates structured output, token accounting, Decimal cost calculations,
error taxonomy mapping, and ensures AI_ENABLED=false cannot accidentally activate.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
import httpx

from app.core.config import settings
from app.ai.types import AIResponseStatus, EpistemicClass
from app.ai.providers.errors import (
    ProviderErrorCode,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ProviderTimeoutError,
    ProviderInvalidResponseError,
)
from app.ai.providers.models import AIProviderRequest, AIProviderResult
from app.ai.providers.openai_provider import OpenAIProvider


@pytest.fixture
def mock_request():
    return AIProviderRequest(
        question="Why did AWS spend increase?",
        system_prompt="System instructions",
        user_prompt="User query and evidence context",
        context_json='{"total_spend": 161000}',
        evidence_hash="abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        model="gpt-4o-mini",
        request_id="req-openai-01",
    )


@pytest.mark.asyncio
async def test_openai_provider_blocked_when_ai_disabled(mock_request, monkeypatch):
    """Proves OpenAI provider is blocked when AI_ENABLED=False even if key is present."""
    monkeypatch.setattr(settings, "AI_ENABLED", False)

    provider = OpenAIProvider(api_key="sk-real-looking-key")
    result: AIProviderResult = await provider.generate_candidate(mock_request)

    assert result.status == AIResponseStatus.PROVIDER_ERROR
    assert result.error_code == ProviderErrorCode.PROVIDER_UNAVAILABLE
    assert "AI is currently disabled" in result.error_message


@pytest.mark.asyncio
async def test_openai_provider_missing_api_key(mock_request, monkeypatch):
    """Proves missing API key results in ProviderAuthenticationError."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)

    provider = OpenAIProvider(api_key="")
    result = await provider.generate_candidate(mock_request)

    assert result.status == AIResponseStatus.PROVIDER_ERROR
    assert result.error_code == ProviderErrorCode.AUTHENTICATION_ERROR
    assert "API key is not configured" in result.error_message


@pytest.mark.asyncio
async def test_openai_provider_successful_structured_completion(mock_request, monkeypatch):
    """Tests 200 OK parsing into AICandidateAnswer with authoritative tokens and Decimal cost."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)

    mock_json_content = {
        "summary": "Spend increased due to EKS expansion.",
        "answer": "Amazon EKS accounted for ₹82,000 of the growth.",
        "conclusions": [
            {
                "statement": "EKS was the largest driver.",
                "epistemic_class": "OBSERVED",
                "evidence_ids": ["ev-eks-1"],
                "numeric_claims": [
                    {"value": "82000.00", "unit": "INR", "evidence_id": "ev-eks-1"}
                ],
            }
        ],
        "limitations": ["Cost Explorer data lags by up to 48 hours."],
        "recommended_next_steps": ["Review EKS node groups."],
    }

    mock_openai_response = {
        "id": "chatcmpl-test12345",
        "choices": [
            {
                "message": {"content": json.dumps(mock_json_content)},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 1200,
            "completion_tokens": 300,
            "total_tokens": 1500,
        },
    }

    mock_http_response = MagicMock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_openai_response

    provider = OpenAIProvider(api_key="sk-test-key-valid")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_http_response
        result = await provider.generate_candidate(mock_request)

    assert result.status == AIResponseStatus.COMPLETED
    assert result.provider == "openai"
    assert result.input_tokens == 1200
    assert result.output_tokens == 300
    assert result.total_tokens == 1500
    assert isinstance(result.estimated_cost_usd, Decimal)
    assert result.estimated_cost_usd > Decimal("0.0000")

    candidate = result.candidate_answer
    assert candidate.summary == "Spend increased due to EKS expansion."
    assert len(candidate.conclusions) == 1
    assert candidate.conclusions[0].epistemic_class == EpistemicClass.OBSERVED
    assert candidate.conclusions[0].numeric_claims[0].value == Decimal("82000.00")


@pytest.mark.asyncio
async def test_openai_provider_timeout_mapping(mock_request, monkeypatch):
    """Proves httpx.TimeoutException maps to ProviderTimeoutError with TIMEOUT status."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)

    provider = OpenAIProvider(api_key="sk-test-key", timeout_seconds=5)

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timeout")):
        result = await provider.generate_candidate(mock_request)

    assert result.status == AIResponseStatus.PROVIDER_ERROR
    assert result.error_code == ProviderErrorCode.TIMEOUT
    assert "timed out after 5 seconds" in result.error_message


@pytest.mark.asyncio
async def test_openai_provider_rate_limit_429(mock_request, monkeypatch):
    """Proves HTTP 429 maps to ProviderRateLimitError with RATE_LIMITED status."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429

    provider = OpenAIProvider(api_key="sk-test-key")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await provider.generate_candidate(mock_request)

    assert result.status == AIResponseStatus.RATE_LIMITED
    assert result.error_code == ProviderErrorCode.RATE_LIMIT


@pytest.mark.asyncio
async def test_openai_provider_auth_failure_401(mock_request, monkeypatch):
    """Proves HTTP 401 maps to ProviderAuthenticationError."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 401

    provider = OpenAIProvider(api_key="sk-bad-key")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await provider.generate_candidate(mock_request)

    assert result.status == AIResponseStatus.PROVIDER_ERROR
    assert result.error_code == ProviderErrorCode.AUTHENTICATION_ERROR


@pytest.mark.asyncio
async def test_openai_provider_service_unavailable_503(mock_request, monkeypatch):
    """Proves HTTP 503 maps to ProviderUnavailableError."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 503

    provider = OpenAIProvider(api_key="sk-test-key")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await provider.generate_candidate(mock_request)

    assert result.status == AIResponseStatus.PROVIDER_ERROR
    assert result.error_code == ProviderErrorCode.PROVIDER_UNAVAILABLE


@pytest.mark.asyncio
async def test_openai_provider_malformed_json_response(mock_request, monkeypatch):
    """Proves non-JSON body maps to ProviderInvalidResponseError."""
    monkeypatch.setattr(settings, "AI_ENABLED", True)

    mock_resp_data = {
        "id": "chatcmpl-invalid",
        "choices": [
            {
                "message": {"content": "This is raw prose, not valid JSON."},
                "finish_reason": "stop",
            }
        ],
    }
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_resp_data

    provider = OpenAIProvider(api_key="sk-test-key")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await provider.generate_candidate(mock_request)

    assert result.status == AIResponseStatus.PROVIDER_ERROR
    assert result.error_code == ProviderErrorCode.INVALID_RESPONSE
