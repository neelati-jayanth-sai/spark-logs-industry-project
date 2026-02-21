"""Deterministic severity calculation from ECS Excel case data."""

from __future__ import annotations

import logging
from io import BytesIO

import pandas as pd

from src.errors.exceptions import AgentError
from src.managers.storage_manager import StorageManager


class SeverityManager:
    """Calculates severity from historical case counts."""

    def __init__(self, storage_manager: StorageManager, sheet_name: str) -> None:
        """Initialize dependencies."""
        self._storage_manager = storage_manager
        self._sheet_name = sheet_name
        self._logger = logging.getLogger("src.managers.severity")

    def classify_severity(self, error_type: str, error_message: str, root_cause: str) -> tuple[str, int]:
        """Count matches and classify severity: 0 low, <5 medium, else high."""
        case_df = self._load_case_dataframe()
        if case_df.empty:
            self._logger.info("severity_cases_empty sheet=%s", self._sheet_name)
            return "low", 0

        normalized = self._normalize_columns(case_df)
        required_columns = {"error_type", "error_message", "root_cause"}
        if not required_columns.issubset(set(normalized.columns)):
            missing = required_columns - set(normalized.columns)
            raise AgentError(f"Severity Excel missing required columns: {sorted(missing)}")

        target_error_type = self._normalize_value(error_type)
        target_error_message = self._normalize_value(error_message)
        target_root_cause = self._normalize_value(root_cause)

        matched = normalized[
            (normalized["error_type"].astype(str).map(self._normalize_value) == target_error_type)
            & (normalized["error_message"].astype(str).map(self._normalize_value) == target_error_message)
            & (normalized["root_cause"].astype(str).map(self._normalize_value) == target_root_cause)
        ]
        count = int(len(matched))
        severity = self._severity_from_count(count)
        self._logger.info("severity_resolved count=%s severity=%s", count, severity)
        return severity, count

    def _load_case_dataframe(self) -> pd.DataFrame:
        """Load case data from Excel file bytes in ECS."""
        raw_excel = self._storage_manager.fetch_severity_cases_excel()
        if not raw_excel:
            return pd.DataFrame()
        try:
            return pd.read_excel(BytesIO(raw_excel), sheet_name=self._sheet_name)
        except Exception as error:  # noqa: BLE001
            raise AgentError(f"Failed to parse severity Excel sheet '{self._sheet_name}': {error}") from error

    @classmethod
    def _normalize_columns(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names for matching."""
        renamed = df.copy()
        renamed.columns = [str(column).strip().lower() for column in renamed.columns]
        return renamed

    @classmethod
    def _normalize_value(cls, value: str) -> str:
        """Normalize values for deterministic matching."""
        return " ".join(str(value).strip().lower().split())

    @classmethod
    def _severity_from_count(cls, count: int) -> str:
        """Map count to severity band."""
        if count == 0:
            return "low"
        if count < 5:
            return "medium"
        return "high"

