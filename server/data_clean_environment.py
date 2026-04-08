"""
Data Cleaning Environment Implementation.

Provides tabular data cleaning tasks where an AI agent fixes data quality issues
through a sequence of cleaning actions. Each episode presents a dirty dataset,
and the agent must clean it by applying actions like fill_missing, convert_type,
remove_duplicates, replace_value, drop_rows, and standardize.
"""

import copy
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from models import DataCleanAction, DataCleanObservation
except ImportError:
    from ..models import DataCleanAction, DataCleanObservation

try:
    from tasks.task_data import DEFAULT_TASK, get_task, grade_task, list_tasks
except ImportError:
    from ..tasks.task_data import DEFAULT_TASK, get_task, grade_task, list_tasks

logger = logging.getLogger(__name__)


def _parse_value(val_str: str) -> Any:
    """Try to parse a string value into the most appropriate Python type."""
    if val_str is None:
        return None
    s = str(val_str).strip()
    if s.lower() in ("none", "null", ""):
        return None
    # Try int
    try:
        return int(s)
    except (ValueError, TypeError):
        pass
    # Try float
    try:
        return float(s)
    except (ValueError, TypeError):
        pass
    return s


def _compute_column_info(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Compute per-column metadata."""
    if not data:
        return {}
    columns = list(data[0].keys())
    info = {}
    for col in columns:
        values = [row.get(col) for row in data]
        types = set(type(v).__name__ for v in values if v is not None)
        null_count = sum(1 for v in values if v is None)
        non_null = [v for v in values if v is not None]
        unique_count = len(set(str(v) for v in non_null))
        info[col] = {
            "dtypes": list(types),
            "null_count": null_count,
            "unique_count": unique_count,
            "total_count": len(values),
        }
    return info


def _validate_column(data: List[Dict[str, Any]], column: str) -> Optional[str]:
    """Return error message if column doesn't exist, else None."""
    if not data:
        return "Error: dataset is empty"
    if column not in data[0]:
        available = list(data[0].keys())
        return f"Error: column '{column}' not found. Available columns: {available}"
    return None


def _apply_action(data: List[Dict[str, Any]], action: DataCleanAction) -> tuple:
    """Apply an action to the data. Returns (new_data, result_message)."""

    if action.action_type == "replace_value":
        if not action.column or action.old_value is None or action.new_value is None:
            return data, "Error: replace_value requires column, old_value, and new_value"
        col_err = _validate_column(data, action.column)
        if col_err:
            return data, col_err
        count = 0
        for row in data:
            if action.column in row and row[action.column] is not None and str(row[action.column]) == action.old_value:
                row[action.column] = _parse_value(action.new_value)
                count += 1
        return data, f"Replaced {count} occurrences of '{action.old_value}' with '{action.new_value}' in column '{action.column}'"

    elif action.action_type == "convert_type":
        if not action.column or not action.target_type:
            return data, "Error: convert_type requires column and target_type"
        col_err = _validate_column(data, action.column)
        if col_err:
            return data, col_err
        count = 0
        errors = 0
        for row in data:
            if action.column not in row or row[action.column] is None:
                continue
            try:
                val = row[action.column]
                if action.target_type == "int":
                    row[action.column] = int(float(str(val)))
                elif action.target_type == "float":
                    row[action.column] = float(str(val))
                elif action.target_type == "str":
                    row[action.column] = str(val)
                count += 1
            except (ValueError, TypeError):
                errors += 1
        msg = f"Converted {count} values in '{action.column}' to {action.target_type}"
        if errors:
            msg += f" ({errors} conversion errors — fix those values first)"
        return data, msg

    elif action.action_type == "fill_missing":
        if not action.column or action.value is None:
            return data, "Error: fill_missing requires column and value"
        col_err = _validate_column(data, action.column)
        if col_err:
            return data, col_err
        count = 0
        fill_val = _parse_value(action.value)
        for row in data:
            if action.column in row and (row[action.column] is None or str(row[action.column]).strip() == ""):
                row[action.column] = fill_val
                count += 1
        return data, f"Filled {count} missing values in '{action.column}' with '{action.value}'"

    elif action.action_type == "remove_duplicates":
        cols = action.subset_columns or (list(data[0].keys()) if data else [])
        seen = set()
        new_data = []
        for row in data:
            key = tuple(str(row.get(c, "")) for c in cols)
            if key not in seen:
                seen.add(key)
                new_data.append(row)
        removed = len(data) - len(new_data)
        return new_data, f"Removed {removed} duplicate rows (checked columns: {cols})"

    elif action.action_type == "drop_rows":
        if not action.row_indices:
            return data, "Error: drop_rows requires row_indices"
        indices = set(action.row_indices)
        invalid = [i for i in indices if i < 0 or i >= len(data)]
        if invalid:
            return data, f"Error: invalid row indices {invalid} (data has {len(data)} rows, valid: 0-{len(data)-1})"
        new_data = [row for i, row in enumerate(data) if i not in indices]
        return new_data, f"Dropped {len(indices)} rows at indices {sorted(indices)}"

    elif action.action_type == "standardize":
        if not action.column or not action.method:
            return data, "Error: standardize requires column and method"
        col_err = _validate_column(data, action.column)
        if col_err:
            return data, col_err
        count = 0
        for row in data:
            if action.column in row and isinstance(row[action.column], str):
                if action.method == "lowercase":
                    row[action.column] = row[action.column].lower()
                elif action.method == "uppercase":
                    row[action.column] = row[action.column].upper()
                elif action.method == "trim":
                    row[action.column] = row[action.column].strip()
                elif action.method == "title_case":
                    row[action.column] = row[action.column].strip().title()
                count += 1
        return data, f"Standardized {count} values in '{action.column}' using '{action.method}'"

    elif action.action_type == "parse_date":
        if not action.column:
            return data, "Error: parse_date requires column"
        col_err = _validate_column(data, action.column)
        if col_err:
            return data, col_err
        count = 0
        import datetime
        formats = ["%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
        for row in data:
            if action.column in row and isinstance(row[action.column], str):
                val = row[action.column].strip()
                for fmt in formats:
                    try:
                        dt = datetime.datetime.strptime(val, fmt)
                        row[action.column] = dt.strftime("%Y-%m-%d")
                        count += 1
                        break
                    except ValueError:
                        pass
        return data, f"Parsed {count} dates in '{action.column}' to YYYY-MM-DD"

    else:
        return data, f"Error: unknown action_type '{action.action_type}'"


class DataCleanEnvironment(Environment):
    """
    Data Cleaning environment for tabular data quality tasks.

    Each episode presents a dirty dataset with specific quality issues. The agent
    applies cleaning actions and receives rewards based on how many issues are fixed.

    Tasks:
    - fix_types (easy): Fix type casting errors in 5-row employee data
    - handle_missing (medium): Handle nulls, duplicates, casing in 10-row product data
    - full_pipeline (hard): All issues combined in 15-row customer order data
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the data cleaning environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_data: List[Dict[str, Any]] = []
        self._task_name: Optional[str] = None
        self._task_config: Optional[Dict[str, Any]] = None
        self._current_score: float = 0.0
        self._max_steps: int = 15

    def reset(
        self,
        task_name: Optional[str] = None,
        episode_id: Optional[str] = None,
    ) -> DataCleanObservation:
        """
        Reset the environment with a specific task.

        Args:
            task_name: One of 'fix_types', 'handle_missing', 'full_pipeline'.
                      Defaults to 'fix_types' if not specified.
            episode_id: Optional episode ID.

        Returns:
            DataCleanObservation with task description and initial data state.
        """
        task_name = task_name or DEFAULT_TASK
        self._task_config = get_task(task_name)
        self._task_name = task_name
        self._current_data = self._task_config["dirty_data"]  # already deep-copied
        self._max_steps = self._task_config["max_steps"]

        self._state = State(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
        )

        # Compute initial score
        self._current_score = grade_task(task_name, self._current_data)
        total_checks = self._task_config["total_checks"]
        issues_fixed = int(round(self._current_score * total_checks))

        return DataCleanObservation(
            task_name=task_name,
            task_description=self._task_config["description"],
            current_data=copy.deepcopy(self._current_data),
            column_info=_compute_column_info(self._current_data),
            row_count=len(self._current_data),
            total_issues=total_checks,
            issues_fixed=issues_fixed,
            last_action_result=None,
            score=self._current_score,
            done=False,
            reward=0.0,
        )

    def step(self, action: DataCleanAction) -> DataCleanObservation:  # type: ignore[override]
        """
        Execute a cleaning action.

        Args:
            action: DataCleanAction specifying the cleaning operation.

        Returns:
            DataCleanObservation with updated data state and reward.
        """
        self._state.step_count += 1

        if self._task_name is None or self._task_config is None:
            return DataCleanObservation(
                task_name=None,
                task_description=None,
                current_data=None,
                column_info=None,
                row_count=0,
                total_issues=0,
                issues_fixed=0,
                last_action_result="Error: call reset() first",
                score=0.0,
                done=True,
                reward=0.0,
            )

        old_score = self._current_score

        # Apply action
        self._current_data, result_msg = _apply_action(self._current_data, action)

        # Compute new score
        self._current_score = grade_task(self._task_name, self._current_data)
        reward = self._current_score - old_score

        total_checks = self._task_config["total_checks"]
        issues_fixed = int(round(self._current_score * total_checks))

        # Check termination
        done = (
            self._current_score >= 1.0
            or self._state.step_count >= self._max_steps
        )

        return DataCleanObservation(
            task_name=self._task_name,
            task_description=None,  # Don't repeat description every step
            current_data=copy.deepcopy(self._current_data),
            column_info=_compute_column_info(self._current_data),
            row_count=len(self._current_data),
            total_issues=total_checks,
            issues_fixed=issues_fixed,
            last_action_result=result_msg,
            score=self._current_score,
            done=done,
            reward=round(reward, 4),
        )

    @property
    def state(self) -> State:
        """Get the current environment state."""
        return self._state
