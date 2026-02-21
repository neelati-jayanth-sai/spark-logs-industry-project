"""Time utility functions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


class TimeUtils:
    """Utility methods for time operations."""

    @classmethod
    def utc_now_iso(cls) -> str:
        """Return current UTC timestamp in ISO 8601."""
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def utc_window_iso(cls, minutes: int) -> tuple[str, str]:
        """Return ISO8601 [from_time, to_time] UTC window."""
        to_dt = datetime.now(timezone.utc)
        from_dt = to_dt - timedelta(minutes=minutes)
        return from_dt.isoformat(), to_dt.isoformat()
