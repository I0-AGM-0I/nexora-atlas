"""
NEXORA ATLAS - Secret Redaction (Phase 9)
Detects and redacts credentials, access keys, tokens, and connection strings.
Preserves meaning and semantic structure (e.g. replaces key with [REDACTED_*]).
"""

import re
from typing import Dict, Any, List

# Compiled secret patterns with standard redaction tokens
SECRET_PATTERNS = [
    # AWS Access Key ID (AKIA...)
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    # AWS IAM Role ARNs
    (re.compile(r"arn:aws:iam::\d{12}:role/[a-zA-Z0-9+=,.@\-_/]+"), "[REDACTED_ROLE_ARN]"),
    # AWS Secret Access Key or session token
    (re.compile(r"(?i)(aws_secret_access_key|aws_session_token)\s*[:=]\s*['\"]?[a-zA-Z0-9/+=]{20,}['\"]?"), "[REDACTED_CREDENTIAL]"),
    # Bearer tokens & JWTs
    (re.compile(r"(?i)bearer\s+ey[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_=]{20,}"), "Bearer [REDACTED_TOKEN]"),
    # Basic Authorization headers
    (re.compile(r"(?i)basic\s+[A-Za-z0-9+/=]{16,}"), "Basic [REDACTED_CREDENTIAL]"),
    # Connection strings (postgres, mysql, mongodb, redis)
    (re.compile(r"(?i)(postgres|postgresql|mysql|mongodb|redis)://[^:]+:([^@]+)@"), r"\1://[USER]:[REDACTED_CREDENTIAL]@"),
    # Generic password / secret assignments
    (re.compile(r"(?i)(password|passwd|secret|api[_-]?key|client[_-]?secret)[\s:=]+['\"]?([A-Za-z0-9\-_=!@#$%^&*]{8,})['\"]?"), r"\1: [REDACTED_SECRET]"),
    # Private Keys (RSA, EC, OpenSSH)
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----"), "[PRIVATE_KEY_REDACTED]"),
]


def redact_secrets(text: str) -> str:
    """
    Sanitizes raw string by replacing all identified credentials with redaction markers.
    Preserves text surrounding secrets to maintain analytical meaning.
    """
    if not text:
        return ""

    sanitized = str(text)
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def redact_data_structure(data: Any) -> Any:
    """
    Recursively scans and redacts secrets in dicts, lists, and strings.
    """
    if isinstance(data, str):
        return redact_secrets(data)
    elif isinstance(data, dict):
        return {k: redact_data_structure(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_data_structure(item) for item in data]
    return data
