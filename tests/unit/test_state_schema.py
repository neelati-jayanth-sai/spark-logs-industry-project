"""Unit tests for state schema."""

from src.state.rca_state import RCAStateFactory, RCAStateValidator


class TestRCAStateSchema:
    """State schema tests."""

    def test_valid_initial_state(self) -> None:
        """Initial state should validate."""
        state = RCAStateFactory.create_initial("job1", "name1", "exec1", "2026-01-01T00:00:00+00:00")
        RCAStateValidator.validate(state)

    def test_missing_key_rejected(self) -> None:
        """Validator should reject missing required key."""
        state = RCAStateFactory.create_initial("job1", "name1", "exec1", "2026-01-01T00:00:00+00:00")
        del state["job_id"]
        try:
            RCAStateValidator.validate(state)
            assert False, "Expected validation error"
        except ValueError:
            assert True

