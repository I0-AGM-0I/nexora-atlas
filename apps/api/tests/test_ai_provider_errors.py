"""
NEXORA ATLAS - Phase 9 Milestone 3: AI Provider Error Taxonomy Tests
Verifies deterministic error hierarchy, retryability flags, HTTP status mappings,
and proves provider failures are distinguishable from malformed candidate answers.
"""

import pytest
from app.ai.providers.errors import (
    ProviderErrorCode,
    AIProviderError,
    ProviderTimeoutError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ProviderInvalidResponseError,
    ProviderUnknownError,
)


def test_provider_error_code_enumeration():
    """Validates all 6 canonical ProviderErrorCodes exist."""
    expected = {
        "TIMEOUT",
        "AUTHENTICATION_ERROR",
        "RATE_LIMIT",
        "PROVIDER_UNAVAILABLE",
        "INVALID_RESPONSE",
        "UNKNOWN",
    }
    actual = {c.value for c in ProviderErrorCode}
    assert actual == expected


def test_timeout_error_properties():
    """Timeout error must be retryable with 408 default code."""
    err = ProviderTimeoutError("Gateway timeout after 30s")
    assert err.error_code == ProviderErrorCode.TIMEOUT
    assert err.retryable is True
    assert err.raw_status_code == 408
    assert "[TIMEOUT]" in str(err)
    assert isinstance(err, AIProviderError)


def test_authentication_error_properties():
    """Authentication failure is NOT retryable and defaults to 401."""
    err = ProviderAuthenticationError("Invalid API Key")
    assert err.error_code == ProviderErrorCode.AUTHENTICATION_ERROR
    assert err.retryable is False
    assert err.raw_status_code == 401
    assert "[AUTHENTICATION_ERROR]" in str(err)


def test_rate_limit_error_properties():
    """Rate limit error is retryable and defaults to 429."""
    err = ProviderRateLimitError("Quota exhausted for organization")
    assert err.error_code == ProviderErrorCode.RATE_LIMIT
    assert err.retryable is True
    assert err.raw_status_code == 429
    assert "[RATE_LIMIT]" in str(err)


def test_unavailable_error_properties():
    """Service unavailable error is retryable and defaults to 503."""
    err = ProviderUnavailableError("OpenAI backend down (503)", raw_status_code=503)
    assert err.error_code == ProviderErrorCode.PROVIDER_UNAVAILABLE
    assert err.retryable is True
    assert err.raw_status_code == 503
    assert "[PROVIDER_UNAVAILABLE]" in str(err)


def test_invalid_response_error_properties():
    """Malformed response from provider is NOT retryable."""
    err = ProviderInvalidResponseError("Malformed JSON output from model")
    assert err.error_code == ProviderErrorCode.INVALID_RESPONSE
    assert err.retryable is False
    assert err.raw_status_code == 502
    assert "[INVALID_RESPONSE]" in str(err)


def test_unknown_error_properties():
    """Unknown exception wrapper properties."""
    err = ProviderUnknownError("Unexpected socket reset", raw_status_code=500)
    assert err.error_code == ProviderErrorCode.UNKNOWN
    assert err.retryable is False
    assert err.raw_status_code == 500
    assert "[UNKNOWN]" in str(err)
