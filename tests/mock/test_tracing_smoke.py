"""Smoke test for callback factory shape."""

from src.config import TelemetryConfig
from src.telemetry.tracers import LangfuseTracerFactory


class TestTracingSmoke:
    """Tracing factory smoke tests."""

    def test_factory_returns_callback_list(self, mocker) -> None:
        """Factory should return callbacks list even with mocked handler."""
        class _Handler:
            def __init__(self, public_key: str, secret_key: str, host: str) -> None:
                self.public_key = public_key
                self.secret_key = secret_key
                self.host = host

        mocker.patch("langfuse.callback.CallbackHandler", _Handler)
        factory = LangfuseTracerFactory(
            TelemetryConfig(public_key="pk", secret_key="sk", host="http://localhost")
        )
        callbacks = factory.create_callbacks()
        assert len(callbacks) == 1
