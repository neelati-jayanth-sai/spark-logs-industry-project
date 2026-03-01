"""LLM manager layer using LangChain primitives."""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from src.schemas.models import AgentResult
from src.errors.exceptions import LLMError
from src.llm.prompts import PromptRegistry


class LLMClient:
    """Single entry point for model invocations."""

    def __init__(self, model: Any, prompt_registry: PromptRegistry, callbacks: list[Any] | None = None) -> None:
        """Initialize with model, prompts, and optional callbacks."""
        self._model = model
        self._prompt_registry = prompt_registry
        self._callbacks = callbacks or []

    def invoke_structured(
        self, prompt_key: str, input_payload: dict[str, Any], output_schema: Type[BaseModel]
    ) -> AgentResult:
        """Invoke model with prompt and structured parser."""
        try:
            prompt = self._prompt_registry.get(prompt_key)
            structured_model = self._model.with_structured_output(output_schema)
            chain = (prompt | structured_model).with_retry(stop_after_attempt=3)
            parsed = chain.invoke(input_payload, config={"callbacks": self._callbacks})
            return AgentResult(
                status=parsed.status,
                data=parsed.data,
                confidence=float(parsed.confidence),
                meta=parsed.meta,
            )
        except Exception as error:  # noqa: BLE001
            raise LLMError(f"LLM structured invocation failed for prompt '{prompt_key}': {error}") from error

    async def ainvoke_structured(
        self, prompt_key: str, input_payload: dict[str, Any], output_schema: Type[BaseModel]
    ) -> AgentResult:
        """Invoke model asynchronously with prompt and structured parser."""
        try:
            prompt = self._prompt_registry.get(prompt_key)
            structured_model = self._model.with_structured_output(output_schema)
            chain = (prompt | structured_model).with_retry(stop_after_attempt=3)
            parsed = await chain.ainvoke(input_payload, config={"callbacks": self._callbacks})
            return AgentResult(
                status=parsed.status,
                data=parsed.data,
                confidence=float(parsed.confidence),
                meta=parsed.meta,
            )
        except Exception as error:  # noqa: BLE001
            raise LLMError(f"Async LLM structured invocation failed for prompt '{prompt_key}': {error}") from error
