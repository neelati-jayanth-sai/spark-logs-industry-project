"""Prompt registry."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


class PromptRegistry:
    """Named prompt templates for reasoning agents."""

    def __init__(self) -> None:
        """Initialize prompt catalog."""
        self._prompts: dict[str, ChatPromptTemplate] = {
            "summarizer": ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a Spark log summarization agent. Return structured JSON only. "
                        "Extract only the primary/root error. Ignore cascading/secondary errors unless no primary error exists. "
                        "In data include keys: summary, error_type, error_message.",
                    ),
                    ("human", "Logs:\n{logs}\n\nContext:\n{context}"),
                ]
            ),
            "category": ChatPromptTemplate.from_messages(
                [
                    ("system", "You classify Spark job failures. Return structured JSON only."),
                    ("human", "Summary:\n{summary}\nRoot cause draft:\n{root_cause}"),
                ]
            ),
            "rca": ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You infer root cause for distributed Spark failures. Return structured JSON only. "
                        "In data include keys: root_cause, rca_category.",
                    ),
                    (
                        "human",
                        "Logs:\n{logs}\nSummary:\n{summary}\nErrorType:\n{error_type}\nErrorMessage:\n{error_message}\n"
                        "Category:\n{category}\nLineage:\n{lineage}\nContext:\n{context}",
                    ),
                ]
            ),
            "solution": ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You generate remediation steps for Spark failures. Return structured JSON only. "
                        "In data include keys: solution, resolution, source. Do not infer severity.",
                    ),
                    (
                        "human",
                        "ErrorType:\n{error_type}\nErrorMessage:\n{error_message}\nRoot cause:\n{root_cause}\n"
                        "Category:\n{category}\nKnown solutions:\n{solutions}",
                    ),
                ]
            ),
        }

    def get(self, key: str) -> ChatPromptTemplate:
        """Get prompt by key."""
        if key not in self._prompts:
            raise KeyError(f"Unknown prompt key: {key}")
        return self._prompts[key]
