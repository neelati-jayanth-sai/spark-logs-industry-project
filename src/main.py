"""CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass

from src.agents.category_agent import CategoryAgent
from src.agents.driver_failure_agent import DriverFailureAgent
from src.agents.lineage_agent import LineageAgent
from src.agents.log_fetcher_agent import LogFetcherAgent
from src.agents.rca_agent import RCAAgent
from src.agents.solution_agent import SolutionAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.config import AppConfig
from src.graph.rca_graph import RCAGraphBuilder
from src.llm.chat_model import ChatModelFactory
from src.llm.prompts import PromptRegistry
from src.managers.iomete_manager import IometeManager
from src.managers.llm_manager import LLMManager
from src.managers.retrieval_manager import RetrievalManager
from src.managers.severity_manager import SeverityManager
from src.managers.splunk_manager import SplunkManager
from src.managers.storage_manager import StorageManager
from src.retrieval.faiss_backend import FaissBackend
from src.storage.s3_storage import S3Storage
from src.system.engine import RCAEngine
from src.telemetry.tracers import LangfuseTracerFactory
from src.utils.logging_utils import LoggingUtils
from src.utils.time_utils import TimeUtils


@dataclass(frozen=True)
class RuntimeComponents:
    """Composed runtime components."""

    config: AppConfig
    engine: RCAEngine
    iomete_manager: IometeManager


class Main:
    """Bootstrap class for runtime composition."""

    @classmethod
    def build_components(cls) -> RuntimeComponents:
        """Build dependency graph and runtime components."""
        config = AppConfig.from_env()
        LoggingUtils.configure(config.logging.level)
        logger = logging.getLogger("src.main")
        logger.info("bootstrap_started")

        tracer_factory = LangfuseTracerFactory(config.telemetry)
        callbacks = tracer_factory.create_callbacks()

        storage = S3Storage(config.storage)
        storage_manager = StorageManager(storage)
        severity_manager = SeverityManager(storage_manager, config.storage.severity_sheet_name)

        retrieval_backend = FaissBackend(config.retrieval.embedding_model)
        retrieval_manager = RetrievalManager(config.retrieval, retrieval_backend)

        model = ChatModelFactory.create(config.llm)
        prompt_registry = PromptRegistry()
        llm_manager = LLMManager(model=model, prompt_registry=prompt_registry, callbacks=callbacks)
        iomete_manager = IometeManager(config.iomete)
        splunk_manager = SplunkManager(config.splunk)

        log_fetcher = LogFetcherAgent(iomete_manager, splunk_manager)
        driver_failure = DriverFailureAgent(iomete_manager)
        lineage = LineageAgent(storage_manager)
        summarizer = SummarizerAgent(llm_manager, retrieval_manager, storage_manager)
        category = CategoryAgent(llm_manager)
        rca = RCAAgent(llm_manager, retrieval_manager, storage_manager)
        solution = SolutionAgent(llm_manager, storage_manager, severity_manager)

        graph_builder = RCAGraphBuilder(
            log_fetcher_agent=log_fetcher,
            driver_failure_agent=driver_failure,
            lineage_agent=lineage,
            summarizer_agent=summarizer,
            category_agent=category,
            rca_agent=rca,
            solution_agent=solution,
        )
        logger.info("bootstrap_completed")
        engine = RCAEngine(graph_builder=graph_builder, callbacks=callbacks)
        return RuntimeComponents(config=config, engine=engine, iomete_manager=iomete_manager)

    @classmethod
    def run(cls) -> None:
        """Parse args, execute engine, print structured state."""
        parser = argparse.ArgumentParser(description="RCA multi-agent diagnostic platform")
        parser.add_argument("--mode", choices=["single", "hourly"], default="single")
        parser.add_argument("--job-id")
        parser.add_argument("--job-name")
        parser.add_argument("--execution-id")
        parser.add_argument("--window-minutes", type=int)
        args = parser.parse_args()

        runtime = cls.build_components()
        if args.mode == "single":
            if not args.job_id or not args.job_name or not args.execution_id:
                raise ValueError("--job-id, --job-name, --execution-id are required in single mode")
            logging.getLogger("src.main").info(
                "cli_execution_started mode=single job_id=%s job_name=%s execution_id=%s",
                args.job_id,
                args.job_name,
                args.execution_id,
            )
            result = runtime.engine.run(job_id=args.job_id, job_name=args.job_name, execution_id=args.execution_id)
            logging.getLogger("src.main").info("cli_execution_completed mode=single status=%s", result["status"])
            print(json.dumps(result, indent=2))
            return

        window_minutes = args.window_minutes or runtime.config.scheduler.window_minutes
        from_time, to_time = TimeUtils.utc_window_iso(window_minutes)
        logger = logging.getLogger("src.main")
        logger.info(
            "cli_execution_started mode=hourly window_minutes=%s from=%s to=%s",
            window_minutes,
            from_time,
            to_time,
        )
        failed_jobs = runtime.iomete_manager.fetch_failed_jobs(from_time=from_time, to_time=to_time)
        results: list[dict[str, object]] = []
        logs_fetched_from_iomete = 0
        logs_fetched_from_splunk = 0
        jobs_failed_due_to_driver_issues = 0
        jobs_without_logs_in_sources = 0
        for failed_job in failed_jobs:
            latest_failed_execution = runtime.iomete_manager.fetch_latest_failed_execution(job_id=failed_job.job_id)
            if latest_failed_execution is None:
                logger.info("hourly_job_skipped job_id=%s reason=no_failed_execution", failed_job.job_id)
                continue
            logger.info(
                "hourly_job_processing job_id=%s job_name=%s execution_id=%s",
                failed_job.job_id,
                failed_job.job_name,
                latest_failed_execution.execution_id,
            )
            try:
                state = runtime.engine.run(
                    job_id=failed_job.job_id,
                    job_name=failed_job.job_name,
                    execution_id=latest_failed_execution.execution_id,
                )
                if state["log_source"] == "iomete":
                    logs_fetched_from_iomete += 1
                elif state["log_source"] == "splunk":
                    logs_fetched_from_splunk += 1
                else:
                    jobs_without_logs_in_sources += 1
                if state["driver_failure"]:
                    jobs_failed_due_to_driver_issues += 1

                results.append(
                    {
                        "job_id": failed_job.job_id,
                        "run_id": latest_failed_execution.execution_id,
                        "job_name": failed_job.job_name,
                        "status": "processed",
                        "RCA_Solution": [
                            {
                                "error_type": state["error_type"],
                                "error_message": state["error_message"],
                                "root_cause": state["root_cause"],
                                "severity": state["severity"],
                                "resolution": state["resolution"],
                                "source": state["solution_source"] or "knowledge_base",
                                "rca_category": state["category"],
                            }
                        ],
                    }
                )
            except Exception as error:  # noqa: BLE001
                logger.exception(
                    "hourly_job_processing_failed job_id=%s execution_id=%s error=%s",
                    failed_job.job_id,
                    latest_failed_execution.execution_id,
                    error,
                )
                results.append(
                    {
                        "job_id": failed_job.job_id,
                        "run_id": latest_failed_execution.execution_id,
                        "job_name": failed_job.job_name,
                        "status": "failed",
                        "RCA_Solution": [],
                    }
                )
        logger.info("cli_execution_completed mode=hourly processed=%s", len(results))
        print(
            json.dumps(
                {
                    "Total failed jobs": len(failed_jobs),
                    "Number of jobs processed": len(results),
                    "Logs fetched from IOMETE": logs_fetched_from_iomete,
                    "Logs fetched from splunk": logs_fetched_from_splunk,
                    "Jobs failed due to driver issues": jobs_failed_due_to_driver_issues,
                    "Number of jobs whose logs are not available in iomete or splunk": jobs_without_logs_in_sources,
                    "results": results,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    Main.run()
