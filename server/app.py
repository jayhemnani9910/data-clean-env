"""
FastAPI application for the Data Cleaning Environment.

Endpoints:
    - POST /reset: Reset the environment with a task
    - POST /step: Execute a cleaning action
    - GET /state: Get current environment state
    - GET /health: Health check
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    uvicorn server.app:app --host 0.0.0.0 --port 7860
"""

import os
import sys

# Ensure repo root is importable when running as a direct script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core[core]"
    ) from e

try:
    from models import DataCleanAction, DataCleanObservation
except ImportError:
    from ..models import DataCleanAction, DataCleanObservation

try:
    from .data_clean_environment import DataCleanEnvironment
except ImportError:
    from data_clean_environment import DataCleanEnvironment

app = create_app(
    DataCleanEnvironment,
    DataCleanAction,
    DataCleanObservation,
    env_name="data_clean_env",
    max_concurrent_envs=5,
)


def main(host: str = "0.0.0.0", port: int = 7860):
    """Run the Data Cleaning environment server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
