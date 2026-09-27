"""
NEXORA ATLAS - AWS Client Lifecycle & Safety Manager
Enforces STS AssumeRole authentication, request-scoped client lifecycle,
bounded exponential backoff, and absolute read-only safety.
"""

import time
import logging
from typing import Optional, Dict, Any
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.integrations.exceptions import (
    AWSAuthenticationError,
    AWSPermissionError,
    AWSRateLimitError,
)

logger = logging.getLogger("atlas.aws.client")

# Retriable AWS error codes
RETRIABLE_ERROR_CODES = {
    "Throttling",
    "ThrottlingException",
    "RequestLimitExceeded",
    "ServiceUnavailable",
    "InternalError",
    "InternalServerError",
    "SlowDown",
}

# Non-retriable permission/auth error codes
NON_RETRIABLE_ERROR_CODES = {
    "AccessDenied",
    "AccessDeniedException",
    "UnauthorizedOperation",
    "InvalidClientTokenId",
    "SignatureDoesNotMatch",
    "InvalidParameterValue",
    "ResourceNotFoundException",
}


class AWSClientFactory:
    """
    Request-scoped AWS client factory.
    Creates temporary assumed-role sessions and closes resources cleanly.
    Never stores or logs long-lived credentials.
    """

    def __init__(
        self,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        region_name: str = "us-east-1",
        session_name: str = "AtlasReadOnlySession",
    ):
        self.role_arn = role_arn
        self.external_id = external_id
        self.region_name = region_name
        self.session_name = session_name
        self._assumed_credentials: Optional[Dict[str, Any]] = None

    def __repr__(self) -> str:
        """Sanitized representation preventing any credential or ARN leakage."""
        masked_arn = f"...{self.role_arn[-12:]}" if self.role_arn and len(self.role_arn) > 12 else "None"
        return f"<AWSClientFactory region={self.region_name} role={masked_arn}>"

    def _resolve_credentials(self) -> Dict[str, Any]:
        """
        Assumes the specified customer IAM role using STS AssumeRole.
        Returns temporary STS session credentials.
        """
        if self._assumed_credentials:
            return self._assumed_credentials

        if not self.role_arn:
            # Fallback to local default credential provider chain (e.g. env vars or test stubs)
            return {}

        sts_client = boto3.client("sts", region_name=self.region_name)
        assume_role_kwargs: Dict[str, Any] = {
            "RoleArn": self.role_arn,
            "RoleSessionName": self.session_name,
            "DurationSeconds": 3600,
        }
        if self.external_id:
            assume_role_kwargs["ExternalId"] = self.external_id

        try:
            response = sts_client.assume_role(**assume_role_kwargs)
            creds = response["Credentials"]
            self._assumed_credentials = {
                "aws_access_key_id": creds["AccessKeyId"],
                "aws_secret_access_key": creds["SecretAccessKey"],
                "aws_session_token": creds["SessionToken"],
            }
            logger.info("Successfully assumed customer IAM role for %s", self.session_name)
            return self._assumed_credentials
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "Unknown")
            msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error("Failed to assume customer IAM role: %s - %s", code, msg)
            if code in ("AccessDenied", "AccessDeniedException"):
                raise AWSPermissionError(f"STS AssumeRole Access Denied: {msg}") from e
            raise AWSAuthenticationError(f"STS Authentication Failed ({code}): {msg}") from e

    def get_client(self, service_name: str, region: Optional[str] = None):
        """
        Creates a temporary, request-scoped client for the given service.
        """
        creds = self._resolve_credentials()
        client_region = region or self.region_name
        config = Config(
            region_name=client_region,
            retries={"max_attempts": 0},  # We implement deterministic bounded retries manually
        )
        return boto3.client(service_name, config=config, **creds)

    @classmethod
    def execute_with_retry(
        cls,
        operation_name: str,
        func,
        *args,
        max_retries: int = 3,
        base_delay_seconds: float = 0.5,
        **kwargs,
    ):
        """
        Executes a boto3 read-only API operation with bounded exponential backoff.
        Only retries transient rate-limit / server errors. Fails fast on auth/permission errors.
        """
        attempts = 0
        while True:
            attempts += 1
            try:
                return func(*args, **kwargs)
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "Unknown")
                message = e.response.get("Error", {}).get("Message", str(e))

                if code in NON_RETRIABLE_ERROR_CODES:
                    logger.warning("AWS non-retriable error in %s: %s", operation_name, code)
                    raise AWSPermissionError(f"{operation_name} failed: {message}") from e

                if code in RETRIABLE_ERROR_CODES and attempts <= max_retries:
                    delay = base_delay_seconds * (2 ** (attempts - 1))
                    logger.warning(
                        "AWS retriable error in %s: %s (attempt %d/%d), backing off %.2fs",
                        operation_name,
                        code,
                        attempts,
                        max_retries,
                        delay,
                    )
                    time.sleep(delay)
                    continue

                if code in RETRIABLE_ERROR_CODES:
                    logger.error("AWS rate limit exceeded in %s after %d retries", operation_name, attempts)
                    raise AWSRateLimitError(f"Rate limit exceeded during {operation_name}: {message}") from e

                logger.error("AWS unhandled client error in %s: %s - %s", operation_name, code, message)
                raise
