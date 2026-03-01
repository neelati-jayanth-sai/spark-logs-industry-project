"""LangChain chat model factory."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from config import LLMConfig


class ChatModelFactory:
    """Factory for LangChain chat models."""

    @classmethod
    def create(cls, config: LLMConfig) -> ChatOpenAI:
        """Create OpenAI-compatible chat model."""
        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            base_url=config.base_url or None,
        )
