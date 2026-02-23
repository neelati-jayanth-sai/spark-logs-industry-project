"""Application configuration models and loader."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMConfig:
    """LLM configuration."""

    api_key: str
    model: str
    temperature: float
    base_url: str


@dataclass(frozen=True)
class StorageConfig:
    """Storage configuration."""

    access_key: str
    secret_key: str
    endpoint: str
    bucket: str
    folder_name: str
    log_key_template: str
    knowledge_key: str
    solutions_key: str
    lineage_key_template: str
    severity_cases_key: str


@dataclass(frozen=True)
class TelemetryConfig:
    """Langfuse telemetry configuration."""

    public_key: str
    secret_key: str
    host: str


@dataclass(frozen=True)
class RetrievalConfig:
    """Retrieval configuration."""

    embedding_model: str
    top_k: int


@dataclass(frozen=True)
class IometeConfig:
    """IOMETE API configuration."""

    base_url: str
    domain_id: str
    api_key: str
    timeout_seconds: int
    logs_endpoint_template: str
    failed_jobs_endpoint_template: str


@dataclass(frozen=True)
class SplunkConfig:
    """Splunk API configuration."""

    host: str
    port: int
    username: str
    password: str
    index: str
    source_type: str
    timeout_seconds: int


@dataclass(frozen=True)
class LoggingConfig:
    """Application logging configuration."""

    level: str


@dataclass(frozen=True)
class SchedulerConfig:
    """Scheduler runtime configuration."""

    window_minutes: int


@dataclass(frozen=True)
class AppConfig:
    """Root app configuration."""

    llm: LLMConfig
    storage: StorageConfig
    telemetry: TelemetryConfig
    retrieval: RetrievalConfig
    iomete: IometeConfig
    splunk: SplunkConfig
    logging: LoggingConfig
    scheduler: SchedulerConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load config values from environment."""
        load_dotenv()
        return cls(
            llm=LLMConfig(
                api_key=os.getenv("LLM_API_KEY", ""),
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0")),
                base_url=os.getenv("LLM_BASE_URL", ""),
            ),
            storage=StorageConfig(
                access_key=os.getenv("ECS_ACCESS_KEY", ""),
                secret_key=os.getenv("ECS_SECRET_KEY", ""),
                endpoint=os.getenv("ECS_ENDPOINT", ""),
                bucket=os.getenv("ECS_BUCKET", ""),
                folder_name=os.getenv("ECS_FOLDER_NAME", ""),
                log_key_template=os.getenv("ECS_LOG_KEY_TEMPLATE", "logs/{job_id}/{run_id}.log"),
                knowledge_key=os.getenv("ECS_KNOWLEDGE_KEY", "knowledge/knowledge.txt"),
                solutions_key=os.getenv("ECS_SOLUTIONS_KEY", "solutions/solutions.txt"),
                lineage_key_template=os.getenv("ECS_LINEAGE_KEY_TEMPLATE", "lineage/{job_name}.json"),
                severity_cases_key=os.getenv("ECS_SEVERITY_CASES_KEY", "severity/case_history.csv"),
            ),
            telemetry=TelemetryConfig(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            ),
            retrieval=RetrievalConfig(
                embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
                top_k=int(os.getenv("RETRIEVAL_TOP_K", "3")),
            ),
            iomete=IometeConfig(
                base_url=os.getenv("IOMETE_BASE_URL", ""),
                domain_id=os.getenv("IOMETE_DOMAIN_ID", ""),
                api_key=os.getenv("IOMETE_API_KEY", ""),
                timeout_seconds=int(os.getenv("IOMETE_TIMEOUT_SECONDS", "30")),
                logs_endpoint_template=os.getenv(
                    "IOMETE_LOGS_ENDPOINT_TEMPLATE",
                    "/api/v1/jobs/{job_id}/runs/{run_id}/logs",
                ),
                failed_jobs_endpoint_template=os.getenv(
                    "IOMETE_FAILED_JOBS_ENDPOINT_TEMPLATE",
                    "/api/v1/domains/{domain_id}/jobs/failed?from={from_time}&to={to_time}",
                ),
            ),
            splunk=SplunkConfig(
                host=os.getenv("SPLUNK_HOST", ""),
                port=int(os.getenv("SPLUNK_PORT", "8089")),
                username=os.getenv("SPLUNK_USERNAME", ""),
                password=os.getenv("SPLUNK_PASSWORD", ""),
                index=os.getenv("SPLUNK_INDEX", ""),
                source_type=os.getenv("SPLUNK_SOURCE_TYPE", ""),
                timeout_seconds=int(os.getenv("SPLUNK_TIMEOUT_SECONDS", "30")),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
            ),
            scheduler=SchedulerConfig(
                window_minutes=int(os.getenv("SCHEDULER_WINDOW_MINUTES", "60")),
            ),
        )
