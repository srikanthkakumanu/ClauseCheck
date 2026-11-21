import json
import logging

import pytest
import structlog

from app.infrastructure.logging import configure_logging
from tests.conftest import SECRET_MARKER


def lines(capsys: pytest.CaptureFixture[str]) -> list[dict]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]


def test_drops_fields_not_on_the_allowlist(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json")
    structlog.get_logger("t").info("review.completed", risk="high", clause=SECRET_MARKER)
    [line] = lines(capsys)
    assert line["risk"] == "high"
    assert "clause" not in line
    assert SECRET_MARKER not in json.dumps(line)


def test_exceptions_keep_type_and_frames_but_not_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO", "json")
    secret_local = SECRET_MARKER  # noqa: F841  # must not appear: no locals in logs
    try:
        raise ValueError(f"input was {SECRET_MARKER}")
    except ValueError:
        structlog.get_logger("t").exception("review.crashed")
    [line] = lines(capsys)
    assert line["exception_type"] == "ValueError"
    assert any("test_logging.py" in frame for frame in line["stack"])
    assert SECRET_MARKER not in json.dumps(line)


def test_stdlib_loggers_use_same_pipeline(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json")
    try:
        raise RuntimeError(SECRET_MARKER)
    except RuntimeError:
        logging.getLogger("uvicorn.error").exception("Exception in ASGI application")
    [line] = lines(capsys)
    assert line["logger"] == "uvicorn.error"
    assert line["exception_type"] == "RuntimeError"
    assert SECRET_MARKER not in json.dumps(line)


def test_request_id_from_context(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json")
    structlog.contextvars.bind_contextvars(request_id="abc123")
    try:
        structlog.get_logger("t").info("x")
    finally:
        structlog.contextvars.clear_contextvars()
    [line] = lines(capsys)
    assert line["request_id"] == "abc123"


def test_level_filters(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("WARNING", "json")
    structlog.get_logger("t").info("hidden")
    structlog.get_logger("t").warning("shown")
    assert [line["event"] for line in lines(capsys)] == ["shown"]


def test_console_format_renders(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "console")
    structlog.get_logger("t").info("review.completed", risk="low", clause=SECRET_MARKER)
    out = capsys.readouterr().out
    assert "review.completed" in out and SECRET_MARKER not in out


def test_uvicorn_access_log_is_off(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json")
    logging.getLogger("uvicorn.access").info('127.0.0.1:5000 - "POST /clauses/review" 200')
    assert capsys.readouterr().out == ""
