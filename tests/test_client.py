"""Tests for client.py payload generation."""

import sys
sys.path.insert(0, ".")
from models import DataCleanAction
from client import DataCleanEnv


def test_step_payload_includes_all_set_fields():
    """_step_payload should include all non-None fields."""
    action = DataCleanAction(
        action_type="replace_value",
        column="age",
        old_value="thirty-five",
        new_value="35",
    )
    payload = DataCleanEnv._step_payload(None, action)
    assert payload == {
        "action_type": "replace_value",
        "column": "age",
        "old_value": "thirty-five",
        "new_value": "35",
    }


def test_step_payload_excludes_none_fields():
    """_step_payload should not include None fields."""
    action = DataCleanAction(
        action_type="parse_date",
        column="hire_date",
    )
    payload = DataCleanEnv._step_payload(None, action)
    assert payload == {
        "action_type": "parse_date",
        "column": "hire_date",
    }
    assert "value" not in payload
    assert "old_value" not in payload
    assert "row_indices" not in payload
