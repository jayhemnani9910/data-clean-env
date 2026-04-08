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
