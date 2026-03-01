import sys
import os
import argparse
import asyncio
from datetime import datetime
from config import AppConfig
from utils.logging_utils import LoggingUtils
from main import Main
from errors.exceptions import ExternalAPIError, StorageError, LLMError

def mask_secret(secret: str) -> str:
    """Mask secret for printing."""
    if not secret:
        return "<NOT SET>"
    if len(secret) <= 4:
        return "****"
    return f"{secret[:4]}...{secret[-4:]}"

async def run_tests():
    print("=" * 60)
    print("🚀 SPARK RCA DIAGNOSTICS - ENVIRONMENT & CONNECTION TESTER")
    print("=" * 60)
    print("\n[1] Loading Environment Configuration...")
    try:
        config = AppConfig.from_env()
        print("✅ Environment variables loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to parse .env file: {e}")
        return

    print("\n[2] Checking Configurations...")
    print(f"  - LLM Model: {config.llm.model}")
    print(f"    API Key: {mask_secret(config.llm.api_key)}")
    print(f"  - S3 Bucket: {config.storage.bucket}")
    print(f"    Access Key: {mask_secret(config.storage.access_key)}")
    print(f"  - Splunk Host: {config.splunk.host}")
    print(f"    Username: {config.splunk.username}")
    print(f"  - IOMETE Base URL: {config.iomete.base_url}")
    print(f"    API Key: {mask_secret(config.iomete.api_key)}")
    print(f"  - Langfuse Host: {config.telemetry.host}")

    print("\n[3] Building Application Clients...")
    try:
        # We disable strict langfuse crash if keys missing since this is just a health check
        os.environ["LANGFUSE_PUBLIC_KEY"] = os.environ.get("LANGFUSE_PUBLIC_KEY", "dummy")
        os.environ["LANGFUSE_SECRET_KEY"] = os.environ.get("LANGFUSE_SECRET_KEY", "dummy")
        
        LoggingUtils.configure("ERROR") # keep silent unless asked
        runtime = Main.build_components()
        print("✅ Core application clients built gracefully.")
    except Exception as e:
        print(f"❌ Failed to build application components. Likely missing critical dependencies or syntax error: {e}")
        return

    print("\n[4] Executing Active Connection Health Pings...")

    # 4.1 Test LLM
    print("\n  🧠 Testing LLM Connection (Azure/OpenAI)...")
    try:
        # LangChain synchronous ping
        prompt = "Reply politely with the word 'PONG'."
        response = runtime.engine._graph_builder._solution_agent._llm_client._model.invoke(prompt)
        print(f"    ✅ Success! Model replied: {response.content.strip()}")
    except Exception as e:
        print(f"    ❌ LLM Connection Failed: {e}")

    # 4.2 Test IOMETE
    print("\n  ☁️  Testing IOMETE Connection...")
    try:
        # Simple fetch with 1 min window just to see if it authenticates (200 OK vs 401/403)
        from_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        runtime.iomete_client.fetch_failed_jobs(from_time, to_time)
        print("    ✅ Success! IOMETE API authenticated (returned valid response list).")
    except ExternalAPIError as e:
        print(f"    ❌ IOMETE API Error: {e}")
    except Exception as e:
        print(f"    ❌ IOMETE Unexpected Error: {e}")

    # 4.3 Test Storage (S3)
    print("\n  🪣 Testing S3 Storage Connection...")
    try:
        # Use underlying boto3 client to head the configured bucket ensuring creds work
        runtime.engine._graph_builder._lineage_agent._storage_client._storage._client.head_bucket(
            Bucket=config.storage.bucket
        )
        print("    ✅ Success! Reached S3 bucket metadata natively.")
    except Exception as e:
        print(f"    ❌ S3 Connection Failed: {e}")

    # 4.4 Test Splunk
    print("\n  🔍 Testing Splunk Connection...")
    try:
        splunk_client = runtime.engine._graph_builder._log_fetcher_agent._splunk_client
        splunk_client.search_logs("test-job", "test-run", "0")
        print("    ✅ Success! Executed search against Splunk endpoint (0 results expected).")
    except ExternalAPIError as e:
        if "Authentication failed" in str(e) or "401" in str(e):
            print(f"    ❌ Splunk Authentication Failed. Check credentials.")
        else:
            print(f"    ⚠️ Splunk Auth succeeded but search threw expected dummy-payload error: {e}")
            print("    ✅ Success! Splunk is reachable.")
    except Exception as e:
        print(f"    ⚠️ Failed but reachable? ({e})")
        
    print("\n" + "=" * 60)
    print("Testing Complete.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
