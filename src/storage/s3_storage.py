"""S3 storage adapter."""

from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from src.config import StorageConfig
from src.errors.exceptions import StorageError


class S3Storage:
    """S3 adapter with typed accessors for required object paths."""

    def __init__(self, config: StorageConfig, client: BaseClient | None = None) -> None:
        """Initialize adapter with dependency injection."""
        self._config = config
        self._client = client or boto3.client(
            "s3",
            endpoint_url=config.endpoint or None,
            aws_access_key_id=config.access_key or None,
            aws_secret_access_key=config.secret_key or None,
        )

    def _full_key(self, key: str) -> str:
        """Prefix key with ECS folder if configured."""
        folder = self._config.folder_name.strip().strip("/")
        clean_key = key.strip().lstrip("/")
        if not folder:
            return clean_key
        return f"{folder}/{clean_key}"

    def _read_text(self, key: str) -> str | None:
        """Read text object from S3, returning None if key does not exist."""
        try:
            response = self._client.get_object(Bucket=self._config.bucket, Key=key)
            body = response["Body"].read().decode("utf-8")
            return body
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404"}:
                return None
            raise StorageError(f"Failed to read S3 object {key}: {error}") from error
        except BotoCoreError as error:
            raise StorageError(f"S3 core failure while reading {key}: {error}") from error

    def _read_json(self, key: str) -> dict[str, Any]:
        """Read JSON object from S3."""
        text = self._read_text(key)
        if text is None:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise StorageError(f"Invalid JSON in S3 object {key}: {error}") from error

    def _read_bytes(self, key: str) -> bytes | None:
        """Read raw bytes object from S3, returning None if key does not exist."""
        try:
            response = self._client.get_object(Bucket=self._config.bucket, Key=key)
            return bytes(response["Body"].read())
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404"}:
                return None
            raise StorageError(f"Failed to read S3 bytes object {key}: {error}") from error
        except BotoCoreError as error:
            raise StorageError(f"S3 core failure while reading bytes {key}: {error}") from error

    def fetch_logs(self, job_id: str, run_id: str) -> str | None:
        """Fetch logs from configured path."""
        key = self._config.log_key_template.format(job_id=job_id, run_id=run_id)
        return self._read_text(self._full_key(key))

    def fetch_knowledge(self) -> str:
        """Fetch RCA knowledge text."""
        return self._read_text(self._full_key(self._config.knowledge_key)) or ""

    def fetch_solutions(self) -> str:
        """Fetch solution knowledge text."""
        return self._read_text(self._full_key(self._config.solutions_key)) or ""

    def fetch_lineage(self, job_name: str) -> dict[str, Any] | None:
        """Fetch lineage JSON."""
        key = self._config.lineage_key_template.format(job_name=job_name)
        payload = self._read_json(self._full_key(key))
        return payload if payload else None

    def fetch_severity_cases_csv(self) -> bytes | None:
        """Fetch severity cases CSV file bytes."""
        return self._read_bytes(self._full_key(self._config.severity_cases_key))
