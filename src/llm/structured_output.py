"""Structured output schemas for reasoning agents."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StructuredAgentOutput(BaseModel):
    """Strict structured output envelope used across all reasoning agents."""

    status: str = Field(description="Execution status")
    data: dict[str, Any] = Field(default_factory=dict, description="Agent payload")
    confidence: float = Field(description="Confidence between 0 and 1")
    meta: dict[str, Any] = Field(default_factory=dict, description="Auxiliary metadata")

