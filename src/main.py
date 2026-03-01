"""CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime

from agents.category_agent import CategoryAgent
from agents.driver_failure_agent import DriverFailureAgent
from agents.lineage_agent import LineageAgent
from agents.log_fetcher_agent import LogFetcherAgent
from agents.rca_agent import RCAAgent
from agents.solution_agent import SolutionAgent
from agents.summarizer_agent import SummarizerAgent
from config import AppConfig
from orchestrator.rca_graph import RCAGraphBuilder
from llm.chat_model import ChatModelFactory
from llm.prompts import PromptRegistry
from clients.iomete_client import IometeClient
from clients.llm_client import LLMClient
from clients.retrieval_client import RetrievalClient
from clients.severity_client import SeverityClient
from clients.splunk_client import SplunkClient
from clients.storage_client import StorageClient
from retrieval.faiss_backend import FaissBackend
from storage.s3_storage import S3Storage
from orchestrator.engine import RCAEngine
from telemetry.tracers import LangfuseTracerFactory
from utils.logging_utils import LoggingUtils
from utils.time_utils import TimeUtils


@dataclass(frozen=True)
class RuntimeComponents:
    """Composed runtime components."""

    config: AppConfig
    engine: RCAEngine
    iomete_client: IometeClient


class Main:
    """Bootstrap class for runtime composition."""

    @classmethod
    def build_components(cls, timestamp: str | None = None) -> RuntimeComponents:
        """Build dependency graph and runtime components."""
        config = AppConfig.from_env()
        LoggingUtils.configure(config.logging.level, timestamp=timestamp)
        logger = logging.getLogger("src.main")
        logger.info("bootstrap_started")

        tracer_factory = LangfuseTracerFactory(config.telemetry)
        callbacks = tracer_factory.create_callbacks()

        storage = S3Storage(config.storage)
        storage_client = StorageClient(storage)
        severity_client = SeverityClient(storage_client)

        retrieval_backend = FaissBackend(config.retrieval.embedding_model)
        retrieval_client = RetrievalClient(config.retrieval, retrieval_backend)

        model = ChatModelFactory.create(config.llm)
        prompt_registry = PromptRegistry()
        llm_client = LLMClient(model=model, prompt_registry=prompt_registry, callbacks=callbacks)
        iomete_client = IometeClient(config.iomete)
        splunk_client = SplunkClient(config.splunk)

        log_fetcher = LogFetcherAgent(iomete_client, splunk_client)
        driver_failure = DriverFailureAgent(iomete_client)
        lineage = LineageAgent(storage_client)
        summarizer = SummarizerAgent(llm_client, retrieval_client, storage_client)
        category = CategoryAgent(llm_client)
        rca = RCAAgent(llm_client, retrieval_client, storage_client)
        solution = SolutionAgent(llm_client, storage_client, severity_client)

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
        engine = RCAEngine(graph_builder=graph_builder, callbacks=callbacks, use_telemetry=True)
        return RuntimeComponents(config=config, engine=engine, iomete_client=iomete_client)

    @classmethod
    async def run(cls) -> None:
        """Parse args, execute engine, print structured state."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        parser = argparse.ArgumentParser(description="RCA multi-agent diagnostic platform")
        parser.add_argument("--mode", choices=["single", "hourly"], default="single")
        parser.add_argument("--job-id")
        parser.add_argument("--job-name")
        parser.add_argument("--run-id")
        parser.add_argument("--window-minutes", type=int)
        parser.add_argument("--output-file", help="Path to save the output JSON", default=f"output_{timestamp_str}.json")
        args = parser.parse_args()

        runtime = cls.build_components(timestamp=timestamp_str)
        if args.mode == "single":
            if not args.job_id or not args.job_name or not args.run_id:
                raise ValueError("--job-id, --job-name, --run-id are required in single mode")
            logging.getLogger("src.main").info(
                "cli_execution_started mode=single job_id=%s job_name=%s run_id=%s",
                args.job_id,
                args.job_name,
                args.run_id,
            )
            result = await runtime.engine.run(job_id=args.job_id, job_name=args.job_name, run_id=args.run_id)
            logging.getLogger("src.main").info("cli_execution_completed mode=single status=%s", result["status"])
            
            logs_content = result.get("logs", "")
            if logs_content:
                logs_filename = f"logs_{args.job_id}_{timestamp_str}.txt"
                with open(logs_filename, "w") as f:
                    f.write(logs_content)
                logging.getLogger("src.main").info("saved raw logs to %s", logs_filename)
                
            # Filter out internal orchestration details
            result.pop("decision_path", None)
            result.pop("agent_history", None)
                
            output_json = json.dumps(result, indent=2)
            print(output_json)
            if args.output_file:
                with open(args.output_file, "w") as f:
                    f.write(output_json)
                logging.getLogger("src.main").info("saved output to %s", args.output_file)
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
        failed_jobs_with_runs = await runtime.iomete_client.fetch_failed_jobs_with_runs_async(
            from_time=from_time, to_time=to_time
        )
        results: list[dict[str, object]] = []
        logs_fetched_from_iomete = 0
        logs_fetched_from_splunk = 0
        jobs_failed_due_to_driver_issues = 0
        jobs_without_logs_in_sources = 0
        
        for failed_job, latest_failed_run in failed_jobs_with_runs:
            logger.info(
                "hourly_job_processing job_id=%s job_name=%s run_id=%s",
                failed_job.job_id,
                failed_job.job_name,
                latest_failed_run.run_id,
            )
            try:
                state = await runtime.engine.run(
                    job_id=failed_job.job_id,
                    job_name=failed_job.job_name,
                    run_id=latest_failed_run.run_id,
                )
                
                logs_content = state.get("logs", "")
                if logs_content:
                    logs_filename = f"logs_{failed_job.job_id}_{timestamp_str}.txt"
                    with open(logs_filename, "w") as f:
                        f.write(logs_content)
                    logger.info("saved raw logs to %s", logs_filename)

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
                        "run_id": latest_failed_run.run_id,
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
                    "hourly_job_processing_failed job_id=%s run_id=%s error=%s",
                    failed_job.job_id,
                    latest_failed_run.run_id,
                    error,
                )
                results.append(
                    {
                        "job_id": failed_job.job_id,
                        "run_id": latest_failed_run.run_id,
                        "job_name": failed_job.job_name,
                        "status": "failed",
                        "RCA_Solution": [],
                    }
                )
        logger.info("cli_execution_completed mode=hourly processed=%s", len(results))
        
        output_data = {
            "Total failed jobs": len(failed_jobs_with_runs),
            "Number of jobs processed": len(results),
            "Logs fetched from IOMETE": logs_fetched_from_iomete,
            "Logs fetched from splunk": logs_fetched_from_splunk,
            "Jobs failed due to driver issues": jobs_failed_due_to_driver_issues,
            "Number of jobs whose logs are not available in iomete or splunk": jobs_without_logs_in_sources,
            "results": results,
        }
        output_json = json.dumps(output_data, indent=2)
        print(output_json)
        
        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(output_json)
            logger.info("saved output to %s", args.output_file)


if __name__ == "__main__":
    import asyncio
    asyncio.run(Main.run())
