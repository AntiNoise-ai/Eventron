"""LLM factory — create LangChain chat models based on configured tiers.

Tiers:
    fast   → DeepSeek (cheapest, good for simple routing)
    smart  → OpenAI GPT-4o-mini (balanced)
    strong → Anthropic Claude Sonnet (complex reasoning)
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from app.config import settings


def create_llm(tier: str | None = None) -> BaseChatModel:
    """Create a LangChain chat model for the given tier.

    Falls back through tiers if a provider's key is missing:
    strong → smart → fast.

    Args:
        tier: 'fast', 'smart', or 'strong'. Defaults to settings.llm_default_tier.

    Returns:
        A LangChain BaseChatModel instance.

    Raises:
        ValueError: If no LLM provider is configured.
    """
    tier = tier or settings.llm_default_tier

    if tier == "strong" and settings.anthropic_api_key and settings.anthropic_api_key != "sk-ant-xxx":
        from langchain_openai import ChatOpenAI
        # Use Anthropic via OpenAI-compatible endpoint isn't standard,
        # use langchain-anthropic if available
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=settings.anthropic_model,
                api_key=settings.anthropic_api_key,
                temperature=0.3,
                max_tokens=2000,
            )
        except ImportError:
            pass  # Fall through to smart

    if tier in ("strong", "smart") and settings.openai_api_key and settings.openai_api_key != "sk-xxx":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
            max_tokens=2000,
        )

    if settings.deepseek_api_key and settings.deepseek_api_key != "sk-xxx":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0.3,
            max_tokens=2000,
        )

    raise ValueError(
        "No LLM provider configured. Set DEEPSEEK_API_KEY, "
        "OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env"
    )


@lru_cache(maxsize=3)
def get_llm(tier: str = "smart") -> BaseChatModel:
    """Cached LLM getter — reuses instances per tier."""
    return create_llm(tier)
