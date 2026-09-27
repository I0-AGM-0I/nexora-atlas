"""
NEXORA ATLAS - AI Prompts Package (Phase 9 Milestone 3)
"""

from app.ai.prompts.versions import (
    PROMPT_SYSTEM_VERSION,
    EXPLANATION_PROMPT_VERSION,
    CONTEXT_VERSION,
)
from app.ai.prompts.system import build_system_prompt, SYSTEM_PROMPT
from app.ai.prompts.templates import build_user_prompt
from app.ai.prompts.builder import PromptBuilder

__all__ = [
    "PROMPT_SYSTEM_VERSION",
    "EXPLANATION_PROMPT_VERSION",
    "CONTEXT_VERSION",
    "SYSTEM_PROMPT",
    "build_system_prompt",
    "build_user_prompt",
    "PromptBuilder",
]
