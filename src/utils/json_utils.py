"""JSON utility helpers."""

from __future__ import annotations

import json
from typing import Any


class JsonUtils:
    """Helpers for JSON-safe conversion and validation."""

    @classmethod
    def ensure_serializable(cls, value: Any) -> Any:
        """Raise if value is not JSON serializable."""
        json.dumps(value)
        return value

