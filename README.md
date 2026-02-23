# RCA Platform: Build From Scratch (Step-by-Step)

This guide shows exactly how to build and run this project from zero.

## 1. Prerequisites

- Python 3.11+ (recommended 3.12)
- Git
- AWS/ECS-compatible object storage credentials
- IOMETE API access
- LLM provider endpoint compatible with OpenAI API
- Langfuse keys

## 2. Create and enter project folder

```bash
mkdir rca
cd rca
```

## 3. Create virtual environment

### Windows PowerShell
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux/macOS
```bash
python -m venv .venv
source .venv/bin/activate
```

## 4. Add dependencies

Create `requirements.txt` and paste current dependencies, then install:

```bash
pip install -r requirements.txt
```

## 5. Create folder structure

Create this structure exactly:

```text
src/
  main.py
  config.py
  system/engine.py
  graph/rca_graph.py
  managers/{storage_manager.py,retrieval_manager.py,llm_manager.py,iomete_manager.py,splunk_manager.py}
  agents/{base_agent.py,log_fetcher_agent.py,driver_failure_agent.py,lineage_agent.py,summarizer_agent.py,category_agent.py,rca_agent.py,solution_agent.py}
  state/rca_state.py
  domain/models.py
  retrieval/{embedding_backend.py,faiss_backend.py}
  storage/s3_storage.py
  llm/{chat_model.py,prompts.py,structured_output.py}
  telemetry/tracers.py
  utils/{time_utils.py,json_utils.py,logging_utils.py}
  errors/exceptions.py
tests/{unit,integration,load,mock}
```

## 6. Implement in this exact order

Follow this order strictly:

1. `domain` models
2. `state` schema
3. `managers`
4. `agents`
5. `graph`
6. `engine`
7. `tracing`

Do not skip ahead.

## 7. Configure environment variables

Copy template:

### Windows
```powershell
Copy-Item .env.example .env
```

### Linux/macOS
```bash
cp .env.example .env
```

Fill these keys in `.env`:

- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_TEMPERATURE`
- `LLM_BASE_URL`
- `ECS_ACCESS_KEY`
- `ECS_SECRET_KEY`
- `ECS_ENDPOINT`
- `ECS_BUCKET`
- `ECS_FOLDER_NAME`
- `ECS_LOG_KEY_TEMPLATE`
- `ECS_KNOWLEDGE_KEY`
- `ECS_SOLUTIONS_KEY`
- `ECS_LINEAGE_KEY_TEMPLATE`
- `ECS_SEVERITY_CASES_KEY`
- `IOMETE_BASE_URL`
- `IOMETE_DOMAIN_ID`
- `IOMETE_API_KEY`
- `IOMETE_TIMEOUT_SECONDS`
- `IOMETE_LOGS_ENDPOINT_TEMPLATE`
- `IOMETE_FAILED_JOBS_ENDPOINT_TEMPLATE`
- `SPLUNK_HOST`
- `SPLUNK_PORT`
- `SPLUNK_USERNAME`
- `SPLUNK_PASSWORD`
- `SPLUNK_INDEX`
- `SPLUNK_SOURCE_TYPE`
- `SPLUNK_TIMEOUT_SECONDS`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST`
- `EMBEDDING_MODEL`
- `RETRIEVAL_TOP_K`
- `LOG_LEVEL`
- `SCHEDULER_WINDOW_MINUTES`

## 8. Validate code compiles

```bash
python -m compileall src tests
```

## 9. Run tests

```bash
pytest -q
```

## 10. Run the application

Single execution mode:

```bash
python -m src.main --mode single --job-id <job_id> --job-name <job_name> --run-id <run_id>
```

Hourly window mode (fetch failed jobs -> latest failed run -> run RCA for each):

```bash
python -m src.main --mode hourly --window-minutes 60
```

## 11. Verify runtime behavior

Check that:

- Output is structured JSON state
- Logs are fetched in order: IOMETE first, Splunk fallback
- Logs are only kept in-memory in graph state (not persisted)
- `driver_failure` comes from IOMETE API call
- `severity` is computed from ECS CSV case history (`count==0 low`, `count<5 medium`, else `high`)
- Traces appear in Langfuse
- Routing is deterministic from state fields
- No LLM calls are made by deterministic agents

## 12. Typical build flow (quick checklist)

1. Setup env + install dependencies
2. Implement modules in required order
3. Configure `.env`
4. Compile
5. Test
6. Run with sample job inputs
7. Validate traces and output
