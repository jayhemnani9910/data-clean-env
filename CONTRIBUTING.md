# Contributing

## Setup

```bash
git clone https://github.com/jayhemnani9910/data-clean-env.git && cd data-clean-env
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt pytest ruff==0.17.4
```

Run the server with `uvicorn server.app:app --port 8000`, or build the image with `docker build -t data-clean-env .`.

## Tests and lint

```bash
python -m pytest -q
ruff check --isolated --select E4,E7,E9,F .
python examples/scripted_policy.py   # with the server running; every task should end at N/N checks
```

CI runs the same three things, the last one against the Docker image.

## Style

Match the code around you. Type hints on new functions. If you add a task, add its dirty table and grader in `tasks/task_data.py`, register it in `TASKS`, add grader tests in `tests/test_graders.py` and a plan in `examples/scripted_policy.py`.

## Branches and pull requests

Branch off `main`, keep one change per PR, and say how you tested it. Commit messages follow `fix:`, `feat:`, `test:`, `docs:`.

## Bugs

Open an issue with the task name, the actions you sent, what you expected and what came back. The bug template asks for this.

I try to reply to issues within a few days.
