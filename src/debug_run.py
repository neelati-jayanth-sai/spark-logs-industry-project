"""Direct manager-level debug runner.

Examples:
    python -m src.debug_run iomete failed-jobs --from-time 2026-02-22T00:00:00Z --to-time 2026-02-22T01:00:00Z
    python -m src.debug_run iomete latest-failed-run --job-id job_123
    python -m src.debug_run iomete logs --job-id job_123 --run-id run_123
    python -m src.debug_run iomete driver-failure --job-id job_123 --run-id run_123
    python -m src.debug_run splunk logs --job-id job_123 --run-id run_123
    python -m src.debug_run storage knowledge
    python -m src.debug_run storage solutions
    python -m src.debug_run storage severity-csv
    python -m src.debug_run severity classify --error-type X --error-message Y --root-cause Z
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from src.config import AppConfig
from src.clients.iomete_client import IometeClient
from src.clients.severity_client import SeverityClient
from src.clients.splunk_client import SplunkClient
from src.clients.storage_client import StorageClient
from src.storage.s3_storage import S3Storage
from src.utils.logging_utils import LoggingUtils


class DebugRun:
    """Manager-level debug entrypoint."""

    def __init__(self) -> None:
        """Build managers from env configuration."""
        self._config = AppConfig.from_env()
        LoggingUtils.configure(self._config.logging.level)
        storage = S3Storage(self._config.storage)
        self._storage_client = StorageClient(storage)
        self._iomete_client = IometeClient(self._config.iomete)
        self._splunk_client = SplunkClient(self._config.splunk)
        self._severity_client = SeverityClient(self._storage_client)

    def run(self, args: argparse.Namespace) -> None:
        """Execute selected debug action."""
        if args.manager == "iomete":
            self._run_iomete(args)
            return
        if args.manager == "splunk":
            self._run_splunk(args)
            return
        if args.manager == "storage":
            self._run_storage(args)
            return
        if args.manager == "severity":
            self._run_severity(args)
            return
        raise ValueError(f"Unsupported manager: {args.manager}")

    def _run_iomete(self, args: argparse.Namespace) -> None:
        """Run IOMETE manager action."""
        if args.action == "failed-jobs":
            data = self._iomete_client.fetch_failed_jobs(from_time=args.from_time, to_time=args.to_time)
            self._print([{"job_id": item.job_id, "job_name": item.job_name} for item in data])
            return
        if args.action == "latest-failed-run":
            data = self._iomete_client.fetch_latest_failed_run(job_id=args.job_id)
            self._print({"run_id": data.run_id} if data else None)
            return
        if args.action == "logs":
            data = self._iomete_client.fetch_logs(job_id=args.job_id, run_id=args.run_id)
            self._print({"logs": data})
            return
        if args.action == "driver-failure":
            data = self._iomete_client.detect_driver_failure(job_id=args.job_id, run_id=args.run_id)
            self._print({"driver_failure": data})
            return
        raise ValueError(f"Unsupported iomete action: {args.action}")

    def _run_splunk(self, args: argparse.Namespace) -> None:
        """Run Splunk manager action."""
        if args.action == "logs":
            data = self._splunk_client.fetch_logs(job_id=args.job_id, run_id=args.run_id)
            self._print({"logs": data})
            return
        raise ValueError(f"Unsupported splunk action: {args.action}")

    def _run_storage(self, args: argparse.Namespace) -> None:
        """Run Storage manager action."""
        if args.action == "knowledge":
            self._print({"knowledge": self._storage_client.fetch_knowledge()})
            return
        if args.action == "solutions":
            self._print({"solutions": self._storage_client.fetch_solutions()})
            return
        if args.action == "severity-csv":
            raw = self._storage_client.fetch_severity_cases_csv()
            self._print({"bytes": len(raw) if raw else 0})
            return
        if args.action == "lineage":
            self._print(self._storage_client.fetch_lineage(job_name=args.job_name))
            return
        raise ValueError(f"Unsupported storage action: {args.action}")

    def _run_severity(self, args: argparse.Namespace) -> None:
        """Run Severity manager action."""
        if args.action == "classify":
            severity, count = self._severity_client.classify_severity(
                error_type=args.error_type,
                error_message=args.error_message,
                root_cause=args.root_cause,
            )
            self._print({"severity": severity, "count": count})
            return
        raise ValueError(f"Unsupported severity action: {args.action}")

    @classmethod
    def _print(cls, payload: Any) -> None:
        """Print JSON output."""
        print(json.dumps(payload, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Direct manager debug runner")
    sub = parser.add_subparsers(dest="manager", required=True)

    iomete = sub.add_parser("iomete")
    iomete_sub = iomete.add_subparsers(dest="action", required=True)
    iomete_failed = iomete_sub.add_parser("failed-jobs")
    iomete_failed.add_argument("--from-time", required=True)
    iomete_failed.add_argument("--to-time", required=True)
    iomete_latest = iomete_sub.add_parser("latest-failed-run")
    iomete_latest.add_argument("--job-id", required=True)
    iomete_logs = iomete_sub.add_parser("logs")
    iomete_logs.add_argument("--job-id", required=True)
    iomete_logs.add_argument("--run-id", required=True)
    iomete_driver = iomete_sub.add_parser("driver-failure")
    iomete_driver.add_argument("--job-id", required=True)
    iomete_driver.add_argument("--run-id", required=True)

    splunk = sub.add_parser("splunk")
    splunk_sub = splunk.add_subparsers(dest="action", required=True)
    splunk_logs = splunk_sub.add_parser("logs")
    splunk_logs.add_argument("--job-id", required=True)
    splunk_logs.add_argument("--run-id", required=True)

    storage = sub.add_parser("storage")
    storage_sub = storage.add_subparsers(dest="action", required=True)
    storage_sub.add_parser("knowledge")
    storage_sub.add_parser("solutions")
    storage_sub.add_parser("severity-csv")
    storage_lineage = storage_sub.add_parser("lineage")
    storage_lineage.add_argument("--job-name", required=True)

    severity = sub.add_parser("severity")
    severity_sub = severity.add_subparsers(dest="action", required=True)
    severity_classify = severity_sub.add_parser("classify")
    severity_classify.add_argument("--error-type", required=True)
    severity_classify.add_argument("--error-message", required=True)
    severity_classify.add_argument("--root-cause", required=True)

    return parser


if __name__ == "__main__":
    cli = build_parser()
    DebugRun().run(cli.parse_args())

