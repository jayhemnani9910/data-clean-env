"""Solve every task with a fixed list of actions. No LLM, no API key.

Start the server first, then:
    python examples/scripted_policy.py [base_url]
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import DataCleanEnv
from models import DataCleanAction

PLANS = {
    "fix_types": [
        {"action_type": "replace_value", "column": "age", "old_value": "thirty-five", "new_value": "35"},
        {"action_type": "replace_value", "column": "salary", "old_value": "ninety thousand", "new_value": "90000"},
        {"action_type": "convert_type", "column": "id", "target_type": "int"},
        {"action_type": "convert_type", "column": "age", "target_type": "int"},
        {"action_type": "convert_type", "column": "salary", "target_type": "int"},
        {"action_type": "parse_date", "column": "hire_date"},
    ],
    "handle_missing": [
        {"action_type": "remove_duplicates", "subset_columns": ["product_id"]},
        {"action_type": "fill_missing", "column": "price", "value": "29.99"},
        {"action_type": "fill_missing", "column": "stock", "value": "0"},
        {"action_type": "fill_missing", "column": "description", "value": "No description"},
        {"action_type": "standardize", "column": "category", "method": "title_case"},
    ],
    "full_pipeline": [
        {"action_type": "remove_duplicates", "subset_columns": ["order_id"]},
        {"action_type": "replace_value", "column": "amount", "old_value": "fifty", "new_value": "50.0"},
        {"action_type": "fill_missing", "column": "amount", "value": "0.0"},
        {"action_type": "fill_missing", "column": "customer_email", "value": "unknown@example.com"},
        {"action_type": "convert_type", "column": "order_id", "target_type": "int"},
        {"action_type": "convert_type", "column": "amount", "target_type": "float"},
        {"action_type": "standardize", "column": "customer_email", "method": "lowercase"},
        {"action_type": "standardize", "column": "status", "method": "title_case"},
        {"action_type": "parse_date", "column": "order_date"},
        {"action_type": "drop_rows", "row_indices": [5]},
    ],
    "outlier_cleanup": [
        {"action_type": "standardize", "column": "product", "method": "trim"},
        {"action_type": "standardize", "column": "product", "method": "title_case"},
        {"action_type": "replace_value", "column": "price", "old_value": "50000.0", "new_value": "500.0"},
        {"action_type": "replace_value", "column": "price", "old_value": "0.0", "new_value": "12.99"},
        {"action_type": "replace_value", "column": "quantity", "old_value": "-2", "new_value": "0"},
        {"action_type": "replace_value", "column": "quantity", "old_value": "100000", "new_value": "100"},
        {"action_type": "drop_rows", "row_indices": [8]},
        {"action_type": "standardize", "column": "currency", "method": "uppercase"},
        {"action_type": "standardize", "column": "region", "method": "title_case"},
    ],
}


def describe(action: dict) -> str:
    args = " ".join(f"{k}={v}" for k, v in action.items() if k != "action_type")
    return f"{action['action_type']} {args}"


async def main(base_url: str) -> None:
    env = DataCleanEnv(base_url=base_url)
    await env.connect()
    try:
        for task, plan in PLANS.items():
            result = await env.reset(task_name=task)
            obs = result.observation
            print(f"\n{task}: {obs.row_count} rows, score {obs.score:.2f}")
            for action in plan:
                result = await env.step(DataCleanAction(**action))
                obs = result.observation
                print(f"  {describe(action):<66} reward {result.reward:+.2f}  score {obs.score:.2f}")
            print(f"  {obs.issues_fixed}/{obs.total_issues} checks pass")
    finally:
        await env.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"))
