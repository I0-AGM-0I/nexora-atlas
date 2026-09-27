"""
NEXORA ATLAS - AI Provider Error Taxonomy (Phase 9 Milestone 3)
Distinguishes connection, authentication, timeout, and availability failures
from candidate response malformations.
"""

from enum import Enum
from typing import Optional


class ProviderErrorCode(str, Enum):
    """Deterministic error codes for AI provider failures."""
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    UNKNOWN = "UNKNOWN"


class AIProviderError(Exception):
    """
    Base exception for all AI provider communication failures.
    Preserves error taxonomy and retryability flags for audit and orchestration.
    """
    def __init__(
        self,
        message: str,
        error_code: ProviderErrorCode = ProviderErrorCode.UNKNOWN,
        raw_status_code: Optional[int] = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.raw_status_code = raw_status_code
        self.retryable = retryable

    def __str__(self) -> str:
        status_info = f" (HTTP {self.raw_status_code})" if self.raw_status_code else ""
        return f"[{self.error_code.value}]{status_info} {self.message}"


class ProviderTimeoutError(AIProviderError):
    """Raised when the provider fails to respond within the configured timeout window."""
    def __init__(self, message: str = "AI provider request timed out", raw_status_code: Optional[int] = None):
        super().__init__(
            message=message,
            error_code=ProviderErrorCode.TIMEOUT,
            raw_status_code=raw_status_code or 408,
            retryable=True,
        )


class ProviderAuthenticationError(AIProviderError):
    """Raised when provider authentication fails (e.g. invalid or missing API key)."""
    def __init__(self, message: str = "AI provider authentication failed", raw_status_code: Optional[int] = None):
        super().__init__(
            message=message,
            error_code=ProviderErrorCode.AUTHENTICATION_ERROR,
            raw_status_code=raw_status_code or 401,
            retryable=False,
        )


class ProviderRateLimitError(AIProviderError):
    """Raised when provider returns HTTP 429 or quota limit exhaustion."""
    def __init__(self, message: str = "AI provider rate limit exceeded", raw_status_code: Optional[int] = None):
        super().__init__(
            message=message,
            error_code=ProviderErrorCode.RATE_LIMIT,
            raw_status_code=raw_status_code or 429,
            retryable=True,
        )


class ProviderUnavailableError(AIProviderError):
    """Raised when provider endpoint is down, unreachable, or returns 502/503/504."""
    def __init__(self, message: str = "AI provider is currently unavailable", raw_status_code: Optional[int] = None):
        super().__init__(
            message=message,
            error_code=ProviderErrorCode.PROVIDER_UNAVAILABLE,
            raw_status_code=raw_status_code or 503,
            retryable=True,
        )


class ProviderInvalidResponseError(AIProviderError):
    """Raised when provider returns non-JSON or unparseable malformed payload."""
    def __init__(self, message: str = "AI provider returned an invalid or malformed response", raw_status_code: Optional[int] = None):
        super().__init__(
            message=message,
            error_code=ProviderErrorCode.INVALID_RESPONSE,
            raw_status_code=raw_status_code or 502,
            retryable=False,
        )


class ProviderUnknownError(AIProviderError):
    """Raised for unexpected exceptions during provider execution."""
    def __init__(self, message: str = "An unknown error occurred during AI provider execution", raw_status_code: Optional[int] = None):
        super().__init__(
            message=message,
            error_code=ProviderErrorCode.UNKNOWN,
            raw_status_code=raw_status_code or 500,
            retryable=False,
        )
