"""Logging configuration utilities."""

from __future__ import annotations

import logging


class LoggingUtils:
    """Utility class for logger configuration."""

    @classmethod
    def configure(cls, level: str) -> None:
        """Configure root logging format and level."""
        normalized_level = (level or "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, normalized_level, logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )

