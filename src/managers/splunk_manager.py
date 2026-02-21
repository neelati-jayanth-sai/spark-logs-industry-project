"""Manager for deterministic Splunk API operations."""

from __future__ import annotations

import logging
from typing import Any

import requests

from src.config import SplunkConfig
from src.errors.exceptions import AgentError


class SplunkManager:
    """Encapsulates Splunk API calls used by deterministic agents."""

    def __init__(self, config: SplunkConfig) -> None:
        """Initialize client settings."""
        self._config = config
        self._logger = logging.getLogger("src.managers.splunk")

    def fetch_logs(self, job_id: str, execution_id: str) -> str | None:
        """Fetch logs from Splunk API."""
        if not self._config.base_url:
            raise AgentError("SPLUNK_BASE_URL is required for Splunk logs")
        endpoint_path = self._config.logs_endpoint_template.format(job_id=job_id, execution_id=execution_id)
        endpoint = f"{self._config.base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
        headers = {"Accept": "application/json"}
        if self._config.token:
            headers["Authorization"] = f"Bearer {self._config.token}"
        try:
            self._logger.info("splunk_logs_request_started endpoint=%s", endpoint)
            response = requests.get(endpoint, headers=headers, timeout=self._config.timeout_seconds)
            if response.status_code == 404:
                self._logger.info("splunk_logs_not_found endpoint=%s", endpoint)
                return None
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            logs_value = payload.get("logs")
            if logs_value is None:
                self._logger.info("splunk_logs_empty endpoint=%s", endpoint)
                return None
            logs = str(logs_value).strip()
            self._logger.info("splunk_logs_request_completed endpoint=%s size=%s", endpoint, len(logs))
            return logs if logs else None
        except requests.RequestException as error:
            self._logger.exception("splunk_logs_request_failed endpoint=%s error=%s", endpoint, error)
            raise AgentError(f"Splunk logs request failed: {error}") from error
        except ValueError as error:
            self._logger.exception("splunk_logs_parse_failed endpoint=%s error=%s", endpoint, error)
            raise AgentError(f"Splunk logs response invalid JSON: {error}") from error

