"""
NEXORA ATLAS - AI Constants (Phase 9)
Defines prompt versions, budgets, thresholds, and token cost calculation constants.
"""

from decimal import Decimal

# Version identifiers for auditing and provenance tracking
AI_SYSTEM_VERSION = "0.1.0"
PROMPT_SYSTEM_VERSION = "atlas-ai-v1"
EXPLANATION_PROMPT_VERSION = "atlas-ai-explanation-v1"
CONTEXT_VERSION = "atlas-ai-context-v1"

# Context and evidence budgeting limits
MAX_EVIDENCE_ITEMS = 100
MAX_RESOURCES = 25
MAX_RECOMMENDATIONS = 25
MAX_SCENARIOS = 10
MAX_TELEMETRY_SUMMARIES = 25
MAX_PERSISTED_EVIDENCE_BYTES = 32768  # 32 KB maximum audit snapshot

# Conversation session memory limits
MAX_SESSION_MESSAGES = 10
MAX_SESSION_CONTEXT_TOKENS = 2000
SESSION_RETENTION_HOURS = 24

# Numerical validation tolerance (1%)
NUMERICAL_TOLERANCE_RATIO = Decimal("0.01")

# Token cost estimation rates per 1,000 tokens (gpt-4o-mini baseline)
INPUT_COST_PER_1K_TOKENS = Decimal("0.000150")   # $0.15 per million
OUTPUT_COST_PER_1K_TOKENS = Decimal("0.000600")  # $0.60 per million
