"""
NEXORA ATLAS - AI Provider Registry (Phase 9 Milestone 3)
Dynamic, vendor-agnostic provider lookup and factory resolution.
Prevents vendor-specific code from leaking into core Atlas intelligence engines.
"""

from typing import Dict, Callable, Optional
from app.core.config import settings
from app.ai.providers.base import AIProvider
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.providers.openai_provider import OpenAIProvider


class ProviderRegistry:
    """
    Registry for AI providers.
    Supports runtime registration and defaults safely to MockAIProvider when AI is disabled.
    """
    _providers: Dict[str, Callable[[], AIProvider]] = {}

    @classmethod
    def register(cls, name: str, factory: Callable[[], AIProvider]) -> None:
        """Registers a provider factory under a unique name."""
        cls._providers[name.lower()] = factory

    @classmethod
    def get_provider(cls, name: Optional[str] = None) -> AIProvider:
        """
        Resolves the configured or requested provider.
        If AI_ENABLED is False or name is unspecified, evaluates settings.AI_PROVIDER.
        Defaults safely to MockAIProvider for offline testing and demo mode.
        """
        target_name = (name or settings.AI_PROVIDER).lower()

        # If provider is explicitly registered, use factory
        if target_name in cls._providers:
            return cls._providers[target_name]()

        # Built-in providers
        if target_name == "openai":
            return OpenAIProvider()
        elif target_name == "mock":
            return MockAIProvider()

        # Fallback to mock for unknown provider names
        return MockAIProvider()

    @classmethod
    def clear(cls) -> None:
        """Clears all dynamically registered provider factories (used in testing)."""
        cls._providers.clear()


# Initialize built-in provider factories
ProviderRegistry.register("mock", lambda: MockAIProvider())
ProviderRegistry.register("openai", lambda: OpenAIProvider())


def get_provider(name: Optional[str] = None) -> AIProvider:
    """Convenience helper to retrieve an AIProvider from ProviderRegistry."""
    return ProviderRegistry.get_provider(name)
