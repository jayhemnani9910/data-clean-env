"""
Data models for the Data Cleaning Environment.

The data_clean_env environment provides tabular data cleaning tasks where an AI agent
must fix data quality issues (type errors, missing values, duplicates, inconsistent
formatting) through a sequence of cleaning actions.
"""

from typing import Any, Dict, List, Literal, Optional

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class DataCleanAction(Action):
    """Action for the Data Cleaning environment.

    The agent selects an action_type and provides the relevant parameters.
    Unused parameters for a given action_type can be left as None.
    """

    action_type: Literal[
        "fill_missing",
        "convert_type",
        "remove_duplicates",
        "replace_value",
        "drop_rows",
        "standardize",
        "parse_date",
    ] = Field(..., description="Type of cleaning action to perform")

    column: Optional[str] = Field(
        None, description="Target column name (required for most actions)"
    )
    value: Optional[str] = Field(
        None, description="Value to fill for fill_missing"
    )
    target_type: Optional[Literal["int", "float", "str"]] = Field(
        None, description="Target type for convert_type action"
    )
    old_value: Optional[str] = Field(
        None, description="Value to find for replace_value"
    )
    new_value: Optional[str] = Field(
        None, description="Replacement value for replace_value"
    )
    row_indices: Optional[List[int]] = Field(
        None, description="Row indices to drop for drop_rows"
    )
    subset_columns: Optional[List[str]] = Field(
        None, description="Columns for remove_duplicates (None = all columns)"
    )
    method: Optional[Literal["lowercase", "trim", "title_case", "uppercase"]] = Field(
        None, description="Standardization method for standardize action"
    )


class DataCleanObservation(Observation):
    """Observation from the Data Cleaning environment."""

    task_name: Optional[str] = Field(
        None, description="Current task name"
    )
    task_description: Optional[str] = Field(
        None, description="Description of what needs to be cleaned"
    )
    current_data: Optional[List[Dict[str, Any]]] = Field(
        None, description="Current state of the data as list of row dicts"
    )
    column_info: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Per-column metadata: dtype, null_count, unique_count"
    )
    row_count: int = Field(0, description="Current number of rows")
    total_issues: int = Field(0, description="Total issues in the task")
    issues_fixed: int = Field(0, description="Number of issues fixed so far")
    last_action_result: Optional[str] = Field(
        None, description="Result message from the last action"
    )
    score: float = Field(0.0, description="Current score [0.0-1.0]")
    # Required by OpenEnv framework — duplicated from StepResult
    done: bool = Field(False, description="Whether the episode is complete")
    reward: float = Field(0.0, description="Reward for the last action")


__all__ = ["DataCleanAction", "DataCleanObservation"]
