"""Logging configuration utilities."""

from __future__ import annotations

import logging


class LoggingUtils:
    """Utility class for logger configuration."""

    @classmethod
    def configure(cls, level: str, timestamp: str | None = None) -> None:
        """Configure root logging format and level."""
        normalized_level = (level or "INFO").upper()
        
        handlers: list[logging.Handler] = [logging.StreamHandler()]
        if timestamp:
            handlers.append(logging.FileHandler(f"execution_{timestamp}.log", mode="a", encoding="utf-8"))
            
        logging.basicConfig(
            level=getattr(logging, normalized_level, logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
            handlers=handlers,
            force=True, # Ensure handlers are reset if configure is called multiple times
        )

