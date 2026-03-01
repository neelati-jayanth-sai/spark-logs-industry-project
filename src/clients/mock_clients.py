"""Mock clients for end-to-end testing."""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from src.schemas.models import AgentResult, FailedJob, FailedRun

class MockSplunkClient:
    def fetch_logs(self, job_id: str, run_id: str) -> str | None:
        return None

class MockIometeClient:
    def detect_driver_failure(self, job_id: str, run_id: str) -> bool:
        return True

    def fetch_logs(self, job_id: str, run_id: str) -> str | None:
        return "java.lang.OutOfMemoryError: Java heap space\\n at org.apache.spark.memory.TaskMemoryManager.allocatePage(TaskMemoryManager.java)"

    def fetch_failed_jobs(self, from_time: str, to_time: str) -> list[FailedJob]:
        return [FailedJob(job_id="MOCK_JOB_1", job_name="Mock Job 1")]

    def fetch_latest_failed_run(self, job_id: str) -> FailedRun | None:
        return FailedRun(run_id="MOCK_RUN_1")

class MockLLMClient:
    def invoke_structured(
        self, prompt_key: str, input_payload: dict[str, Any], output_schema: Type[BaseModel]
    ) -> AgentResult:
        # Default mock population
        data = {}
        for field_name, field in getattr(output_schema, 'model_fields', {}).items():
            ann = field.annotation
            if ann == str:
                data[field_name] = "mock_" + field_name
            elif ann == list[str]:
                data[field_name] = ["mock_item"]
            elif ann == bool:
                data[field_name] = True
            elif ann == dict[str, Any] or ann == dict:
                data[field_name] = {"mock_key": "mock_val"}
            else:
                data[field_name] = None
        if prompt_key == "summarizer":
            data = {"summary": "Mock summary of OOM error.", "error_type": "OutOfMemoryError", "error_message": "Java heap space"}
        elif prompt_key == "category":
            data = {"category": "Memory"}
        elif prompt_key == "rca":
            data = {"root_cause": "Driver ran out of memory.", "error_type": "OutOfMemoryError", "error_message": "Java heap space"}
        elif prompt_key == "solution":
            data = {"solution": "Increase spark.driver.memory.", "resolution": ["Increase memory limit."], "solution_source": "mock_kb"}
            
        # We skip instantiating output_schema to avoid nested wrapper Pydantic validation errors.
        # The mock data dictionary provides all fields the agents look for in result.data.
        return AgentResult(status="success", data=data, confidence=0.99, meta={"mocked": True})

    async def ainvoke_structured(
        self, prompt_key: str, input_payload: dict[str, Any], output_schema: Type[BaseModel]
    ) -> AgentResult:
        return self.invoke_structured(prompt_key, input_payload, output_schema)

class MockRetrievalClient:
    def build_context(self, log_text: str, knowledge_docs: Any) -> dict[str, Any]:
        return {
            "query": str(log_text)[:50],
            "matches": ["Mock knowledge base article about OOM matching this trace."]
        }

class MockStorageClient:
    def fetch_logs(self, job_id: str, run_id: str) -> str | None:
        return None

    def fetch_lineage(self, job_name: str) -> dict[str, Any] | None:
        return {"upstream": ["mock_table_a"], "downstream": ["mock_table_b"]}

    def fetch_knowledge(self) -> str:
        return "Mock Knowledge Document on memory configurations."

    def fetch_solutions(self) -> str:
        return "Mock Solution Document for standard errors."

    def fetch_severity_cases_csv(self) -> bytes | None:
        return b"error_type,error_message,root_cause\\nOutOfMemoryError,Java heap space,Driver ran out of memory\\n"
