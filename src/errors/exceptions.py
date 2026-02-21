"""Typed exceptions for RCA platform layers."""


class RCAException(Exception):
    """Base exception for RCA runtime."""


class StorageError(RCAException):
    """Raised for storage layer failures."""


class RetrievalError(RCAException):
    """Raised for retrieval layer failures."""


class LLMError(RCAException):
    """Raised for LLM invocation failures."""


class GraphError(RCAException):
    """Raised for graph build or execution failures."""


class AgentError(RCAException):
    """Raised for agent-level failures."""

