"""Langfuse tracer factory."""

from __future__ import annotations

from typing import Any

from config import TelemetryConfig


class LangfuseTracerFactory:
    """Creates Langfuse callback handlers for LangChain and LangGraph."""

    def __init__(self, config: TelemetryConfig) -> None:
        """Initialize telemetry config."""
        self._config = config

    def create_callbacks(self, **kwargs: Any) -> list[Any]:
        """Create callback list for framework-native tracing.
        
        Args:
            kwargs: Optional arguments like `session_id`, `trace_name`, etc. passed to Langfuse.
        """
        try:
            from langfuse.callback import CallbackHandler  # type: ignore
        except ImportError:  # pragma: no cover
            from langfuse.langchain import CallbackHandler  # type: ignore

        handler = CallbackHandler(
            public_key=self._config.public_key,
            secret_key=self._config.secret_key,
            host=self._config.host,
            **kwargs
        )
        return [handler]

