"""
NEXORA ATLAS - Integration Exceptions
"""


class IntegrationError(Exception):
    """Base exception for all integration errors."""
    pass


class AWSAuthenticationError(IntegrationError):
    """Raised when STS AssumeRole or credential validation fails."""
    pass


class AWSPermissionError(IntegrationError):
    """Raised when required read-only permissions are denied."""
    pass


class AWSRateLimitError(IntegrationError):
    """Raised when AWS API rate limits or throttling limits are exceeded."""
    pass


class AWSSyncError(IntegrationError):
    """Raised during synchronization failures."""
    pass
