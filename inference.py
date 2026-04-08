"""
Inference Script — Data Cleaning Environment
=============================================
MANDATORY ENV VARS:
    API_BASE_URL   The API endpoint for the LLM (default: https://router.huggingface.co/v1)
    MODEL_NAME     The model identifier (default: Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN       Hugging Face API key (required)
    IMAGE_NAME     Docker image name for the environment (if using from_docker_image)
    ENV_BASE_URL   Base URL of the environment server (default: http://localhost:7860)

STDOUT FORMAT:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import asyncio
import json
import os
import textwrap
import time
from typing import Dict, List, Optional

from openai import OpenAI

try:
    from data_clean_env import DataCleanAction, DataCleanEnv
except ImportError:
    from client import DataCleanEnv
    from models import DataCleanAction

try:
    from data_clean_env.tasks.task_data import list_tasks, TASKS as TASK_CONFIGS
except ImportError:
    from tasks.task_data import list_tasks, TASKS as TASK_CONFIGS

IMAGE_NAME = os.getenv("IMAGE_NAME")
API_KEY = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")
BENCHMARK = "data_clean_env"

TEMPERATURE = 0.3
MAX_TOKENS = 800

FALLBACK_ACTIONS: Dict[str, dict] = {
    "fix_types": {"action_type": "convert_type", "column": "id", "target_type": "int"},
    "handle_missing": {"action_type": "remove_duplicates", "subset_columns": ["product_id"]},
    "full_pipeline": {"action_type": "remove_duplicates", "subset_columns": ["order_id"]},
    "outlier_cleanup": {"action_type": "standardize", "column": "product", "method": "trim"},
}


# --- Logging ----------------------------------------------------------------

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# --- LLM Agent --------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""\
You are a data cleaning agent. You receive a dirty dataset and must fix data quality issues.

You respond with a SINGLE JSON object representing one cleaning action. No explanation, no markdown, just JSON.

Available action_types and their required fields:
1. "replace_value": column, old_value, new_value — find and replace specific values
2. "convert_type": column, target_type ("int"|"float"|"str") — convert column type
3. "fill_missing": column, value — fill None/null/empty values
4. "remove_duplicates": subset_columns (list of column names, or null for all)
5. "drop_rows": row_indices (list of int indices to drop)
6. "standardize": column, method ("lowercase"|"uppercase"|"trim"|"title_case")
7. "parse_date": column — convert mixed date formats to YYYY-MM-DD

Example response:
{"action_type": "replace_value", "column": "age", "old_value": "thirty-five", "new_value": "35"}

IMPORTANT:
- Return ONLY valid JSON, no markdown code fences, no explanation
- Fix issues in logical order: replace text values first, then convert types
- Only include fields relevant to your chosen action_type
""")


def build_user_prompt(
    task_desc: str,
    data: list,
    column_info: dict,
    row_count: int,
    issues_fixed: int,
    total_issues: int,
    score: float,
    last_result: Optional[str],
    step: int,
    history: List[str],
) -> str:
    data_preview = json.dumps(data, indent=2, default=str)
    col_info_str = json.dumps(column_info, indent=2, default=str)
    history_str = "\n".join(history[-5:]) if history else "None"

    return textwrap.dedent(f"""\
Task: {task_desc}

Current data ({row_count} rows, showing all):
{data_preview}

Column info:
{col_info_str}

Progress: {issues_fixed}/{total_issues} issues fixed, score={score:.2f}
Step: {step}
Last action result: {last_result or 'None (first step)'}

Recent history:
{history_str}

Return your next cleaning action as a single JSON object.
""")


def get_action_from_llm(client: OpenAI, user_prompt: str, task_name: str = "fix_types", max_retries: int = 2) -> dict:
    """Call the LLM and parse the JSON action. Retries on failure."""
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            text = (completion.choices[0].message.content or "").strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            return json.loads(text)
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))
                print(f"[DEBUG] LLM attempt {attempt + 1} failed: {exc}, retrying...", flush=True)

    print(f"[DEBUG] LLM failed after {max_retries + 1} attempts: {last_exc}", flush=True)
    return FALLBACK_ACTIONS.get(task_name, {"action_type": "convert_type", "column": "id", "target_type": "int"})


# --- Main Loop --------------------------------------------------------------

async def run_task(client: OpenAI, env: DataCleanEnv, task_name: str) -> float:
    """Run a single task and return the final score."""
    max_steps = TASK_CONFIGS[task_name]["max_steps"]
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task_name=task_name)
        obs = result.observation

        history: List[str] = []

        for step in range(1, max_steps + 1):
            if result.done:
                break

            user_prompt = build_user_prompt(
                task_desc=obs.task_description or "",
                data=obs.current_data or [],
                column_info=obs.column_info or {},
                row_count=obs.row_count,
                issues_fixed=obs.issues_fixed,
                total_issues=obs.total_issues,
                score=obs.score,
                last_result=obs.last_action_result,
                step=step,
                history=history,
            )

            action_dict = get_action_from_llm(client, user_prompt, task_name=task_name)
            action_str = json.dumps(action_dict, default=str)

            try:
                action = DataCleanAction(**action_dict)
            except Exception as e:
                print(f"[DEBUG] Invalid action: {e}", flush=True)
                action_dict = FALLBACK_ACTIONS.get(task_name, {"action_type": "convert_type", "column": "id", "target_type": "int"})
                action = DataCleanAction(**action_dict)
                action_str = json.dumps(action_dict, default=str)

            result = await env.step(action)
            obs = result.observation

            reward = result.reward or 0.0
            done = result.done
            error = None

            rewards.append(reward)
            steps_taken = step
            score = obs.score

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append(f"Step {step}: {action_str} -> reward={reward:+.2f}, score={score:.2f}")

            if done:
                break

        success = score >= 0.5

    except Exception as exc:
        print(f"[DEBUG] Task error: {exc}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main() -> None:
    if not API_KEY:
        raise ValueError("HF_TOKEN environment variable is required")
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    if IMAGE_NAME:
        env = await DataCleanEnv.from_docker_image(IMAGE_NAME)
    else:
        env = DataCleanEnv(base_url=ENV_BASE_URL)
        await env.connect()

    try:
        for task_name in list_tasks():
            await run_task(client, env, task_name)
    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
