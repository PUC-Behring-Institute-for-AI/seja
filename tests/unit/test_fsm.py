import pytest
from statemachine.exceptions import TransitionNotAllowed

from seja_mcp.lifecycle_fsm import SejaLifecycleFSM


def _get_state_value(fsm):
    return list(fsm.configuration)[0].value


def _set_state_value(fsm, value):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        fsm.current_state = getattr(fsm, value)


class TestInitialState:
    def test_initial_state(self):
        fsm = SejaLifecycleFSM()
        assert _get_state_value(fsm) == "setup"


class TestForwardTransitions:
    def test_setup_to_design_blocked_when_no_constitution(self, mock_get_db):
        fsm = SejaLifecycleFSM()
        fsm.context = {"workspace_path": "/test", "project_id": "p1", "get_db": mock_get_db}
        with pytest.raises(TransitionNotAllowed):
            fsm.setup_to_design()
        assert _get_state_value(fsm) == "setup"

    def test_setup_to_design_succeeds_with_constitution(self, mock_get_db_with_constitution):
        fsm = SejaLifecycleFSM()
        fsm.context = {"workspace_path": "/test", "project_id": "p1", "get_db": mock_get_db_with_constitution}
        fsm.setup_to_design()
        assert _get_state_value(fsm) == "design"

    def test_design_to_research_blocked_when_no_features(self, mock_get_db):
        fsm = SejaLifecycleFSM()
        fsm.context = {"workspace_path": "/test", "project_id": "p1", "get_db": mock_get_db}
        _set_state_value(fsm, "design")
        with pytest.raises(TransitionNotAllowed):
            fsm.design_to_research()
        assert _get_state_value(fsm) == "design"


class TestReverseTransitions:
    def test_reverse_requires_reason(self):
        fsm = SejaLifecycleFSM()
        fsm.context = {"project_id": "p1", "reason": ""}
        _set_state_value(fsm, "implement")
        with pytest.raises(TransitionNotAllowed):
            fsm.implement_to_design()

    def test_reverse_succeeds_with_reason(self, mock_get_db):
        fsm = SejaLifecycleFSM()
        fsm.context = {"project_id": "p1", "reason": "Scope changed", "get_db": mock_get_db}
        _set_state_value(fsm, "implement")
        fsm.implement_to_design()
        assert _get_state_value(fsm) == "design"


class TestGuardConditions:
    def test_constitution_not_empty_guard_false(self, mock_get_db):
        fsm = SejaLifecycleFSM()
        fsm.context = {"project_id": "p1", "get_db": mock_get_db}
        assert fsm.constitution_not_empty() is False

    def test_constitution_not_empty_with_data(self, mock_get_db_with_constitution):
        fsm = SejaLifecycleFSM()
        fsm.context = {"project_id": "p1", "get_db": mock_get_db_with_constitution}
        assert fsm.constitution_not_empty() is True

    def test_reason_provided_true(self):
        fsm = SejaLifecycleFSM()
        fsm.context = {"reason": "because"}
        assert fsm.reason_provided() is True

    def test_reason_provided_false(self):
        fsm = SejaLifecycleFSM()
        fsm.context = {"reason": ""}
        assert fsm.reason_provided() is False

    def test_reason_provided_none(self):
        fsm = SejaLifecycleFSM()
        fsm.context = {}
        assert fsm.reason_provided() is False
