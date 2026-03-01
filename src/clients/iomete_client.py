"""Manager for deterministic IOMETE API operations."""

from __future__ import annotations

import logging
from typing import Any

import requests

from config import IometeConfig
from schemas.models import FailedJob, FailedRun
from errors.exceptions import AgentError


class IometeClient:
    """Encapsulates IOMETE API calls used by deterministic agents."""

    def __init__(self, config: IometeConfig) -> None:
        """Initialize client settings."""
        self._config = config
        self._logger = logging.getLogger("src.clients.iomete")

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {"Accept": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        return headers

    def _build_endpoint(self, template: str, **kwargs: str) -> str:
        """Build full URL from endpoint template."""
        if not self._config.base_url:
            raise AgentError("IOMETE_BASE_URL is required")
        path = template.format(**kwargs)
        return f"{self._config.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _get_json(self, endpoint: str) -> dict[str, Any]:
        """GET endpoint and parse JSON payload."""
        try:
            self._logger.info("iomete_request_started endpoint=%s", endpoint)
            response = requests.get(endpoint, headers=self._headers(), timeout=self._config.timeout_seconds)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            self._logger.info("iomete_request_completed endpoint=%s status_code=%s", endpoint, response.status_code)
            return payload
        except requests.RequestException as error:
            self._logger.exception("iomete_request_failed endpoint=%s error=%s", endpoint, error)
            raise AgentError(f"IOMETE API request failed: {error}") from error
        except ValueError as error:
            self._logger.exception("iomete_response_parse_failed endpoint=%s error=%s", endpoint, error)
            raise AgentError(f"IOMETE API returned invalid JSON: {error}") from error

    def detect_driver_failure(self, job_id: str, run_id: str) -> bool:
        """Call IOMETE API to determine driver failure status."""
        endpoint = self._build_endpoint(
            "/api/v1/jobs/{job_id}/runs/{run_id}/driver-failure",
            job_id=job_id,
            run_id=run_id,
        )
        payload = self._get_json(endpoint)
        if "driver_failure" not in payload:
            raise AgentError("IOMETE API response missing 'driver_failure' field")
        result = bool(payload["driver_failure"])
        self._logger.info(
            "iomete_driver_failure_resolved endpoint=%s driver_failure=%s",
            endpoint,
            result,
        )
        return result

    def fetch_logs(self, job_id: str, run_id: str) -> str | None:
        """Fetch logs from IOMETE API."""
        endpoint = self._build_endpoint(
            self._config.logs_endpoint_template,
            job_id=job_id,
            run_id=run_id,
        )
        try:
            self._logger.info("iomete_logs_request_started endpoint=%s", endpoint)
            response = requests.get(endpoint, headers=self._headers(), timeout=self._config.timeout_seconds)
            if response.status_code == 404:
                self._logger.info("iomete_logs_not_found endpoint=%s", endpoint)
                return None
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            logs_value = payload.get("logs")
            if logs_value is None:
                self._logger.info("iomete_logs_empty endpoint=%s", endpoint)
                return None
            logs = str(logs_value).strip()
            self._logger.info("iomete_logs_request_completed endpoint=%s size=%s", endpoint, len(logs))
            return logs if logs else None
        except requests.RequestException as error:
            self._logger.exception("iomete_logs_request_failed endpoint=%s error=%s", endpoint, error)
            raise AgentError(f"IOMETE logs request failed: {error}") from error
        except ValueError as error:
            self._logger.exception("iomete_logs_parse_failed endpoint=%s error=%s", endpoint, error)
            raise AgentError(f"IOMETE logs response invalid JSON: {error}") from error

    def fetch_failed_jobs(self, from_time: str, to_time: str) -> list[FailedJob]:
        """Fetch failed jobs for a time window."""
        endpoint = self._build_endpoint(
            self._config.failed_jobs_endpoint_template,
            domain_id=self._config.domain_id,
            from_time=from_time,
            to_time=to_time,
        )
        payload = self._get_json(endpoint)
        raw_jobs = payload.get("jobs", payload if isinstance(payload, list) else [])
        if not isinstance(raw_jobs, list):
            raise AgentError("IOMETE failed jobs response must contain a list")
        results: list[FailedJob] = []
        for item in raw_jobs:
            if not isinstance(item, dict):
                continue
            job_id = str(item.get("job_id", "")).strip()
            job_name = str(item.get("job_name", job_id)).strip()
            if not job_id:
                continue
            results.append(FailedJob(job_id=job_id, job_name=job_name or job_id))
        self._logger.info("iomete_failed_jobs_resolved from=%s to=%s count=%s", from_time, to_time, len(results))
        return results

    def fetch_latest_failed_run(self, job_id: str) -> FailedRun | None:
        """Fetch latest failed run for a job."""
        if not self._config.domain_id:
            raise AgentError("IOMETE_DOMAIN_ID is required for latest failed run lookup")
        endpoint = self._build_endpoint(
            "/api/v1/domains/{domain_id}/jobs/{job_id}/runs/latest-failed",
            domain_id=self._config.domain_id,
            job_id=job_id,
        )
        payload = self._get_json(endpoint)
        raw_run_id = payload.get("run_id", payload.get("execution_id"))
        if raw_run_id is None:
            return None
        run_id = str(raw_run_id).strip()
        if not run_id:
            return None
        self._logger.info("iomete_latest_failed_run_resolved job_id=%s run_id=%s", job_id, run_id)
        return FailedRun(run_id=run_id)

    async def fetch_failed_jobs_with_runs_async(self, from_time: str, to_time: str) -> list[tuple[FailedJob, FailedRun]]:
        """Fetch all jobs, then concurrently find latest failed runs for each."""
        try:
            import aiohttp
            import asyncio
            from datetime import datetime
        except ImportError as e:
            self._logger.error("aiohttp required for async fetch. Please install it.")
            raise AgentError("Missing async dependencies") from e

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            jobs_endpoint = self._config.base_url.rstrip("/") + "/api/v1/jobs"
            self._logger.info("iomete_fetch_all_jobs_started endpoint=%s", jobs_endpoint)
            
            async with session.get(jobs_endpoint, headers=self._headers()) as resp:
                if resp.status == 404:
                    jobs_endpoint = self._build_endpoint("/api/v1/domains/{domain_id}/jobs", domain_id=self._config.domain_id)
                    async with session.get(jobs_endpoint, headers=self._headers()) as resp2:
                        resp2.raise_for_status()
                        jobs_payload = await resp2.json()
                else:
                    resp.raise_for_status()
                    jobs_payload = await resp.json()
                    
            jobs = jobs_payload if isinstance(jobs_payload, list) else jobs_payload.get("jobs", [])
            self._logger.info("iomete_fetch_all_jobs_completed count=%s", len(jobs))
            
            if not jobs:
                return []

            semaphore = asyncio.Semaphore(100)
            
            async def _process_single_job(job: dict) -> tuple[FailedJob, FailedRun] | None:
                async with semaphore:
                    job_id = job.get("id", job.get("job_id"))
                    job_name = job.get("name", job.get("job_name", "Unnamed"))
                    if not job_id:
                        return None
                        
                    runs_endpoint = self._config.base_url.rstrip("/") + f"/api/v1/jobs/{job_id}/runs?status=&start={from_time}&end={to_time}"
                    
                    try:
                        async with session.get(runs_endpoint, headers=self._headers()) as r:
                            if r.status != 200:
                                return None
                            runs_payload = await r.json()
                    except Exception:
                        return None
                        
                    runs = runs_payload if isinstance(runs_payload, list) else runs_payload.get("runs", [])
                    if not runs:
                        return None
                        
                    runs_with_time = []
                    for run in runs:
                        term_time_str = run.get("terminationTime")
                        if term_time_str:
                            try:
                                dt = datetime.fromisoformat(term_time_str.replace("Z", "+00:00"))
                                runs_with_time.append((run, dt))
                            except Exception:
                                continue
                                
                    if not runs_with_time:
                        return None
                        
                    runs_with_time.sort(key=lambda x: x[1], reverse=True)
                    latest_run, _ = runs_with_time[0]
                    
                    run_id = latest_run.get("id", latest_run.get("run_id"))
                    driver_status = latest_run.get("driverStatus", latest_run.get("status", ""))
                    
                    if driver_status in ["FAILED", "ABORTED"] and run_id:
                        return FailedJob(job_id=job_id, job_name=job_name), FailedRun(run_id=run_id)
                    return None

            tasks = [_process_single_job(job) for job in jobs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_results = []
            for res in results:
                if isinstance(res, tuple) and len(res) == 2:
                    valid_results.append(res)
                    
            self._logger.info("iomete_failed_jobs_resolved from=%s to=%s count=%s", from_time, to_time, len(valid_results))
            return valid_results
