"""Manager for deterministic Splunk API operations."""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from src.config import SplunkConfig
from src.errors.exceptions import AgentError


class SplunkClient:
    """Encapsulates Splunk API calls used by deterministic agents."""

    def __init__(self, config: SplunkConfig) -> None:
        """Initialize client settings."""
        self._config = config
        self._logger = logging.getLogger("src.clients.splunk")

    def fetch_logs(self, job_id: str, run_id: str) -> str | None:
        """Fetch logs from Splunk API."""
        if not self._config.host:
            raise AgentError("SPLUNK_HOST is required for Splunk logs")
        endpoint = f"https://{self._config.host}:{self._config.port}/services/search/jobs/export"
        headers = {"Accept": "application/json"}
        search_query = (
            f"search index={self._config.index} sourcetype={self._config.source_type} "
            f"job_id={job_id} run_id={run_id}"
        )
        params = {"output_mode": "json", "search": search_query}
        try:
            self._logger.info("splunk_logs_request_started endpoint=%s", endpoint)
            response = requests.get(
                endpoint,
                headers=headers,
                params=params,
                auth=HTTPBasicAuth(self._config.username, self._config.password),
                timeout=self._config.timeout_seconds,
                verify=False,
            )
            if response.status_code == 404:
                self._logger.info("splunk_logs_not_found endpoint=%s", endpoint)
                return None
            response.raise_for_status()
            text = response.text.strip()
            if not text:
                self._logger.info("splunk_logs_empty endpoint=%s", endpoint)
                return None
            # Splunk export can return line-delimited JSON; keep raw text for summarization.
            logs = text
            self._logger.info("splunk_logs_request_completed endpoint=%s size=%s", endpoint, len(logs))
            return logs if logs else None
        except requests.RequestException as error:
            self._logger.exception("splunk_logs_request_failed endpoint=%s error=%s", endpoint, error)
            raise AgentError(f"Splunk logs request failed: {error}") from error
        except ValueError as error:
            self._logger.exception("splunk_logs_parse_failed endpoint=%s error=%s", endpoint, error)
            raise AgentError(f"Splunk logs response invalid JSON: {error}") from error
