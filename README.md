---
title: Data Clean Environment
emoji: 🧹
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# DataCleanEnv — Data Cleaning RL Environment

An OpenEnv-compliant reinforcement learning environment where an AI agent learns to clean messy tabular data through a sequence of structured cleaning actions.

## Overview

Real-world data is messy. This environment simulates common data quality issues — type errors, missing values, duplicates, inconsistent formatting — that data engineers fix daily. An AI agent must learn to identify and fix these issues efficiently.

## Tasks

| Task | Difficulty | Rows | Issues | Description |
|------|-----------|------|--------|-------------|
| `fix_types` | Easy | 5 | 9 | Fix type casting errors in employee records |
| `handle_missing` | Medium | 10 | 6 | Handle nulls, duplicates, inconsistent casing in product inventory |
| `full_pipeline` | Hard | 15 | 12 | All issues combined in customer order data |
| `outlier_cleanup` | Medium-Hard | 10 | 10 | Fix outliers, inconsistent casing, and data anomalies in sales data |

## Action Space

| Action Type | Required Fields | Description |
|-------------|----------------|-------------|
| `replace_value` | column, old_value, new_value | Find and replace specific values |
| `convert_type` | column, target_type | Convert column to int/float/str |
| `fill_missing` | column, value | Fill None/empty values |
| `remove_duplicates` | subset_columns | Remove duplicate rows |
| `drop_rows` | row_indices | Drop rows by index |
| `standardize` | column, method | Apply lowercase/uppercase/trim/title_case |
| `parse_date` | column | Convert mixed date formats to YYYY-MM-DD |

## Observation Space

Each observation includes:
- **task_description**: What needs to be cleaned
- **current_data**: Current data rows as list of dicts
- **column_info**: Per-column metadata (dtypes, null counts, unique counts)
- **row_count**: Number of rows
- **score**: Current quality score [0.0–1.0]
- **issues_fixed / total_issues**: Progress tracking
- **last_action_result**: Feedback from the last action

## Reward Function

- Each check passed = `1/total_checks` of the score
- Reward per step = `new_score - old_score` (positive for fixes, negative for breaking data)
- Episode ends when score = 1.0 or max steps reached

## Example Episode Trace

```
POST /reset {"task_name": "fix_types"}
← score=0.11, issues_fixed=1/9

POST /step {"action_type": "replace_value", "column": "age", "old_value": "thirty-five", "new_value": "35"}
← reward=0.00, score=0.11, "Replaced 1 occurrences..."

POST /step {"action_type": "replace_value", "column": "salary", "old_value": "ninety thousand", "new_value": "90000"}
← reward=0.00, score=0.11, "Replaced 1 occurrences..."

POST /step {"action_type": "convert_type", "column": "id", "target_type": "int"}
← reward=0.11, score=0.22, "Converted 5 values..."

POST /step {"action_type": "convert_type", "column": "age", "target_type": "int"}
← reward=0.22, score=0.44, "Converted 5 values..."

POST /step {"action_type": "convert_type", "column": "salary", "target_type": "int"}
← reward=0.22, score=0.67, "Converted 5 values..."

POST /step {"action_type": "parse_date", "column": "hire_date"}
← reward=0.33, score=1.00, done=true
```

## Setup

### Docker (Recommended)

```bash
cd data_clean_env
docker build -t data-clean-env:latest .
docker run --rm -p 7860:7860 data-clean-env:latest
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{}'
```

### Local Development

```bash
cd data_clean_env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

## Running Inference

```bash
export HF_TOKEN="your-hf-token"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export IMAGE_NAME="data-clean-env:latest"
python inference.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/reset` | Reset environment with task_name parameter |
| POST | `/step` | Execute a cleaning action |
| GET | `/state` | Get current episode state |
| GET | `/health` | Health check |

## Baseline Scores

| Task | Baseline Score | Steps Used |
|------|---------------|------------|
| fix_types | ~0.78 | 8 |
| handle_missing | ~0.83 | 6 |
| full_pipeline | ~0.58 | 15 |
| outlier_cleanup | ~0.60 | 12 |

## Project Structure

```
data_clean_env/
├── server/
│   ├── app.py                      # FastAPI server
│   └── data_clean_environment.py   # Environment implementation
├── tasks/
│   └── task_data.py                # Task data and graders
├── models.py                       # Pydantic Action/Observation models
├── client.py                       # OpenEnv client
├── inference.py                    # Baseline inference script
├── openenv.yaml                    # OpenEnv spec
├── Dockerfile                      # Container config
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Hardware Requirements

- 2 vCPU, 8 GB RAM
- Inference runtime < 20 minutes
