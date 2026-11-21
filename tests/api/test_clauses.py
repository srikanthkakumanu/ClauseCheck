"""End-to-end through HTTP with ask_llm patched: no network, no key."""

import json
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.application.errors import ModelReplyInvalid, ModelUnavailable
from app.application.review_clause import DISCLAIMER
from app.infrastructure import openai_review_model
from app.infrastructure.llm import LlmReply
from app.main import create_app
from tests.conftest import CLAUSE, CLAUSE_WITH_MARKER, SECRET_MARKER, reply_json

URL = "/clauses/review"


@pytest.fixture
def patch_llm(monkeypatch: pytest.MonkeyPatch) -> Callable[[Any], list[str]]:
    """Patch ask_llm to return a reply (str) or raise an error; returns the list of calls."""

    def install(result: Any) -> list[str]:
        calls: list[str] = []

        def fake_ask_llm(system_prompt: str, user_text: str, *args: Any, **kwargs: Any) -> LlmReply:
            calls.append(user_text)
            if isinstance(result, Exception):
                raise result
            return LlmReply(text=result, model="test-model", tokens_in=10, tokens_out=5)

        monkeypatch.setattr(openai_review_model, "ask_llm", fake_ask_llm)
        return calls

    return install


@pytest.fixture
def client(capsys: pytest.CaptureFixture[str]) -> TestClient:
    # Built inside the test so logging writes to the captured stdout.
    return TestClient(create_app(), raise_server_exceptions=False)


def test_happy_path(client: TestClient, patch_llm) -> None:
    calls = patch_llm(reply_json())
    resp = client.post(URL, json={"clause": CLAUSE})
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk"] == "high"
    assert body["disclaimer"] == DISCLAIMER
    assert all(issue["excerpt"] in CLAUSE for issue in body["issues"])
    assert set(body) == {"risk", "summary", "issues", "disclaimer"}
    assert calls == [CLAUSE]


@pytest.mark.parametrize(
    "payload",
    [
        {"clause": "too short"},
        {"clause": "x" * 4001},
        {"clause": " " * 50},
        {},
        {"clause": 12345},
        {"clause": CLAUSE, "extra": "field"},
        ["not", "an", "object"],
    ],
)
def test_bad_requests_are_400_and_never_call_the_model(
    client: TestClient, patch_llm, payload: Any
) -> None:
    calls = patch_llm(reply_json())
    resp = client.post(URL, json=payload)
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_clause"
    assert calls == []


def test_non_json_body_is_400(client: TestClient, patch_llm) -> None:
    patch_llm(reply_json())
    resp = client.post(URL, content=b"clause=hello", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_clause"


def test_400_never_echoes_input(client: TestClient, patch_llm) -> None:
    patch_llm(reply_json())
    resp = client.post(URL, json={"clause": 1, "note": SECRET_MARKER})
    assert SECRET_MARKER not in resp.text


@pytest.mark.parametrize(
    ("result", "code"),
    [
        (ModelUnavailable("the model call failed"), "model_unavailable"),
        (ModelReplyInvalid("the model refused to review the clause"), "model_reply_invalid"),
        ("not json", "model_reply_invalid"),
        (json.dumps({"risk": "safe", "summary": "Fine.", "issues": []}), "model_reply_invalid"),
        (
            reply_json(issues=[{"excerpt": "unlimited liability", "concern": "Invented."}]),
            "ungrounded_issue",
        ),
    ],
)
def test_model_problems_are_502(client: TestClient, patch_llm, result: Any, code: str) -> None:
    patch_llm(result)
    resp = client.post(URL, json={"clause": CLAUSE})
    assert resp.status_code == 502
    assert resp.json()["error"] == code
    assert "disclaimer" not in resp.json()


def test_request_id_is_generated_or_reused(client: TestClient, patch_llm) -> None:
    patch_llm(reply_json())
    generated = client.post(URL, json={"clause": CLAUSE}).headers["X-Request-ID"]
    assert len(generated) == 32
    reused = client.post(URL, json={"clause": CLAUSE}, headers={"X-Request-ID": "abc-123_X"})
    assert reused.headers["X-Request-ID"] == "abc-123_X"
    unsafe = client.post(URL, json={"clause": CLAUSE}, headers={"X-Request-ID": "a b\n{evil}"})
    assert unsafe.headers["X-Request-ID"] != "a b\n{evil}"


def log_lines(capsys: pytest.CaptureFixture[str]) -> list[dict]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]


def test_one_access_line_per_request(
    client: TestClient, patch_llm, capsys: pytest.CaptureFixture[str]
) -> None:
    patch_llm(reply_json())
    resp = client.post(URL, json={"clause": CLAUSE})
    lines = log_lines(capsys)
    access = [line for line in lines if line["event"] == "request.completed"]
    assert len(access) == 1
    assert access[0]["status"] == 200
    assert access[0]["request_id"] == resp.headers["X-Request-ID"]
    assert {"method", "path", "latency_ms"} <= set(access[0])
    completed = [line for line in lines if line["event"] == "review.completed"]
    assert completed[0]["request_id"] == resp.headers["X-Request-ID"]


@pytest.mark.parametrize(
    "result",
    [
        reply_json(summary=f"Mentions {SECRET_MARKER}."),
        ModelUnavailable("the model call failed"),
        f"not json {SECRET_MARKER}",
        reply_json(issues=[{"excerpt": f"{SECRET_MARKER} invented", "concern": "Invented."}]),
    ],
)
def test_logs_never_contain_clause_or_reply(
    client: TestClient, patch_llm, capsys: pytest.CaptureFixture[str], result: Any
) -> None:
    patch_llm(result)
    resp = client.post(URL, json={"clause": CLAUSE_WITH_MARKER})
    out = capsys.readouterr().out
    assert out.strip(), "expected log output"
    assert SECRET_MARKER not in out
    assert "terminate this Agreement" not in out
    if resp.status_code != 200:
        assert SECRET_MARKER not in resp.text


def test_unexpected_crash_is_500_without_leaking(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom(*args: Any, **kwargs: Any) -> LlmReply:
        raise RuntimeError(f"bug while handling {SECRET_MARKER}")

    monkeypatch.setattr(openai_review_model, "ask_llm", boom)
    resp = client.post(URL, json={"clause": CLAUSE_WITH_MARKER})
    assert resp.status_code == 500
    out = capsys.readouterr().out
    assert "RuntimeError" in out
    assert SECRET_MARKER not in out
    assert SECRET_MARKER not in resp.text
