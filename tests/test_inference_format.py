"""Tests for inference.py stdout logging format."""


def test_log_start_format():
    """[START] line must match spec format."""
    from inference import log_start
    import io
    import sys

    captured = io.StringIO()
    sys.stdout = captured
    log_start("fix_types", "data_clean_env", "test-model")
    sys.stdout = sys.__stdout__

    line = captured.getvalue().strip()
    assert line == "[START] task=fix_types env=data_clean_env model=test-model"


def test_log_step_format():
    """[STEP] line must match spec format with 2-decimal reward."""
    from inference import log_step
    import io
    import sys

    captured = io.StringIO()
    sys.stdout = captured
    log_step(1, '{"action_type":"convert_type"}', 0.111, False, None)
    sys.stdout = sys.__stdout__

    line = captured.getvalue().strip()
    assert line == '[STEP] step=1 action={"action_type":"convert_type"} reward=0.11 done=false error=null'


def test_log_step_with_error():
    """[STEP] error field should show raw error string."""
    from inference import log_step
    import io
    import sys

    captured = io.StringIO()
    sys.stdout = captured
    log_step(2, '{"action_type":"drop_rows"}', 0.0, False, "invalid index")
    sys.stdout = sys.__stdout__

    line = captured.getvalue().strip()
    assert "error=invalid index" in line


def test_log_end_format():
    """[END] line must match spec format."""
    from inference import log_end
    import io
    import sys

    captured = io.StringIO()
    sys.stdout = captured
    log_end(True, 3, 1.0, [0.0, 0.11, 0.89])
    sys.stdout = sys.__stdout__

    line = captured.getvalue().strip()
    assert line == "[END] success=true steps=3 score=1.00 rewards=0.00,0.11,0.89"


class _FakeResult:
    """Minimal stand-in for the env step/reset result."""

    def __init__(self, last_action_result=None, done=False, reward=0.0, score=0.0):
        from models import DataCleanObservation

        self.observation = DataCleanObservation(
            task_description="test task",
            current_data=[],
            column_info={},
            row_count=0,
            issues_fixed=0,
            total_issues=1,
            score=score,
            last_action_result=last_action_result,
        )
        self.done = done
        self.reward = reward


class _FakeEnv:
    def __init__(self, step_result):
        self._step_result = step_result

    async def reset(self, task_name=None):
        return _FakeResult(done=False)

    async def step(self, action):
        return self._step_result


def _run_task_with_step_result(step_result, monkeypatch, capsys):
    import asyncio

    import inference

    monkeypatch.setitem(inference.TASK_CONFIGS, "test_task", {"max_steps": 3})
    monkeypatch.setattr(
        inference,
        "get_action_from_llm",
        lambda client, prompt, task_name=None: {
            "action_type": "convert_type",
            "column": "nope",
            "target_type": "int",
        },
    )
    env = _FakeEnv(step_result)
    asyncio.run(inference.run_task(None, env, "test_task"))
    return capsys.readouterr().out


def test_run_task_logs_error_from_last_action_result(monkeypatch, capsys):
    """[STEP] must surface an env error instead of always showing error=null."""
    out = _run_task_with_step_result(
        _FakeResult(
            last_action_result="Error: column 'nope' not found", done=True
        ),
        monkeypatch,
        capsys,
    )
    step_lines = [l for l in out.splitlines() if l.startswith("[STEP]")]
    assert step_lines, out
    assert "error=Error: column 'nope' not found" in step_lines[0]


def test_run_task_logs_null_error_for_non_error_result(monkeypatch, capsys):
    """A non-error last_action_result must still log error=null."""
    out = _run_task_with_step_result(
        _FakeResult(last_action_result="Converted column 'id' to int", done=True),
        monkeypatch,
        capsys,
    )
    step_lines = [l for l in out.splitlines() if l.startswith("[STEP]")]
    assert step_lines, out
    assert "error=null" in step_lines[0]
