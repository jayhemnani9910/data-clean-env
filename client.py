"""Data Cleaning Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import DataCleanAction, DataCleanObservation
except ImportError:
    from models import DataCleanAction, DataCleanObservation


class DataCleanEnv(EnvClient[DataCleanAction, DataCleanObservation, State]):
    """
    Client for the Data Cleaning Environment.

    Example::

        async def example():
            env = DataCleanEnv(base_url="http://localhost:7860")
            await env.connect()
            result = await env.reset(task_name="fix_types")
            print(result.observation.task_description)

            result = await env.step(DataCleanAction(
                action_type="replace_value",
                column="age",
                old_value="thirty-five",
                new_value="35",
            ))
            print(f"Score: {result.observation.score}")
            await env.close()

    Example with Docker::

        async def docker_example():
            client = await DataCleanEnv.from_docker_image("data-clean-env:latest")
            try:
                result = await client.reset(task_name="fix_types")
                result = await client.step(DataCleanAction(
                    action_type="convert_type",
                    column="id",
                    target_type="int",
                ))
            finally:
                await client.close()
    """

    def _step_payload(self, action: DataCleanAction) -> Dict:
        """Convert DataCleanAction to JSON payload."""
        payload = {"action_type": action.action_type}
        if action.column is not None:
            payload["column"] = action.column
        if action.value is not None:
            payload["value"] = action.value
        if action.target_type is not None:
            payload["target_type"] = action.target_type
        if action.old_value is not None:
            payload["old_value"] = action.old_value
        if action.new_value is not None:
            payload["new_value"] = action.new_value
        if action.row_indices is not None:
            payload["row_indices"] = action.row_indices
        if action.subset_columns is not None:
            payload["subset_columns"] = action.subset_columns
        if action.method is not None:
            payload["method"] = action.method
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[DataCleanObservation]:
        """Parse server response into StepResult[DataCleanObservation]."""
        obs_data = payload.get("observation", {})
        observation = DataCleanObservation(
            task_name=obs_data.get("task_name"),
            task_description=obs_data.get("task_description"),
            current_data=obs_data.get("current_data"),
            column_info=obs_data.get("column_info"),
            row_count=obs_data.get("row_count", 0),
            total_issues=obs_data.get("total_issues", 0),
            issues_fixed=obs_data.get("issues_fixed", 0),
            last_action_result=obs_data.get("last_action_result"),
            score=obs_data.get("score", 0.0),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """Parse server response into State object."""
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
