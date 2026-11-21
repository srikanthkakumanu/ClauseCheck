"""Traces may carry metadata only: the clause and the model reply must never be sent."""

import json
from typing import Any
from unittest import mock

import langsmith.utils
import pytest
from langsmith import Client, tracing_context

from app.domain.clause import Clause
from app.infrastructure import openai_review_model
from app.infrastructure.llm import LlmReply
from app.infrastructure.openai_review_model import OpenAIReviewModel
from tests.conftest import CLAUSE_WITH_MARKER, SECRET_MARKER, reply_json


def capture_traces(monkeypatch: pytest.MonkeyPatch, hide: bool) -> str:
    """Run one review with tracing on and return everything sent to LangSmith."""
    monkeypatch.setenv("LANGSMITH_HIDE_INPUTS", str(hide).lower())
    monkeypatch.setenv("LANGSMITH_HIDE_OUTPUTS", str(hide).lower())
    langsmith.utils.get_env_var.cache_clear()  # LangSmith caches env lookups per process
    reply = reply_json(summary=f"Summary mentions {SECRET_MARKER}.")
    monkeypatch.setattr(
        openai_review_model,
        "ask_llm",
        lambda *a, **k: LlmReply(text=reply, model="test-model", tokens_in=10, tokens_out=5),
    )
    sent: list[str] = []

    def fake_request(method: str, url: str, *args: Any, **kwargs: Any) -> mock.Mock:
        body = kwargs.get("data") or kwargs.get("json") or b""
        sent.append(body.decode() if isinstance(body, bytes) else json.dumps(body, default=str))
        resp = mock.Mock(status_code=200, ok=True, headers={})
        resp.json.return_value = {}
        return resp

    client = Client(api_key="test", api_url="http://127.0.0.1:9", auto_batch_tracing=False)
    client.session.request = fake_request  # type: ignore[method-assign]
    with tracing_context(enabled=True, client=client):
        OpenAIReviewModel("system prompt").review(Clause(CLAUSE_WITH_MARKER))
    langsmith.utils.get_env_var.cache_clear()
    assert sent, "no trace was sent"
    return "\n".join(sent)


def test_trace_never_contains_clause_or_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = capture_traces(monkeypatch, hide=True)
    assert SECRET_MARKER not in payload
    assert "system prompt" not in payload
    assert '"issue_count"' in payload and '"risk"' in payload  # metadata still arrives


def test_control_without_hide_flags_would_leak(monkeypatch: pytest.MonkeyPatch) -> None:
    # Proves the test above can fail: without the flags, the clause is in the payload.
    assert SECRET_MARKER in capture_traces(monkeypatch, hide=False)
