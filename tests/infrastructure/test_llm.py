from types import SimpleNamespace
from typing import Any

import httpx
import openai
import pytest

from app.application.errors import ModelReplyInvalid, ModelUnavailable
from app.infrastructure import llm
from app.infrastructure.model_reply import REVIEW_REPLY_SCHEMA
from tests.conftest import reply_json


def response(
    text: str | None = None,
    status: str = "completed",
    incomplete: object | None = None,
    refusal: bool = False,
) -> SimpleNamespace:
    content = (
        [SimpleNamespace(type="refusal", refusal="I can't help with that.")]
        if refusal
        else [SimpleNamespace(type="output_text", text=text or "")]
    )
    return SimpleNamespace(
        status=status,
        incomplete_details=incomplete,
        output=[SimpleNamespace(type="message", content=content)],
        output_text="" if refusal else (text if text is not None else reply_json()),
        usage=SimpleNamespace(input_tokens=120, output_tokens=40),
    )


class FakeResponses:
    def __init__(self, result: Any) -> None:
        self.result = result
        self.kwargs: dict[str, Any] = {}

    def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch):
    def install(result: Any) -> FakeResponses:
        responses = FakeResponses(result)
        monkeypatch.setattr(llm, "get_client", lambda: SimpleNamespace(responses=responses))
        return responses

    return install


def test_sends_one_structured_outputs_request(fake) -> None:
    responses = fake(response())
    reply = llm.ask_llm("system prompt", "clause text", REVIEW_REPLY_SCHEMA, "clause_review")
    sent = responses.kwargs
    assert sent["model"] == "test-model"
    assert sent["instructions"] == "system prompt"
    assert sent["input"] == "clause text"
    assert sent["text"]["format"] == {
        "type": "json_schema",
        "name": "clause_review",
        "schema": REVIEW_REPLY_SCHEMA,
        "strict": True,
    }
    assert sent["reasoning"] == {"effort": "low"}
    assert sent["store"] is False
    assert "temperature" not in sent
    assert (reply.tokens_in, reply.tokens_out, reply.model) == (120, 40, "test-model")


def test_reasoning_effort_from_config(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUSECHECK_REASONING_EFFORT", "high")
    responses = fake(response())
    llm.ask_llm("s", "c", REVIEW_REPLY_SCHEMA)
    assert responses.kwargs["reasoning"] == {"effort": "high"}


@pytest.mark.parametrize(
    "error",
    [
        openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com")),
        openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com")),
        openai.AuthenticationError(
            "bad key",
            response=httpx.Response(401, request=httpx.Request("POST", "https://x")),
            body=None,
        ),
    ],
)
def test_sdk_errors_become_model_unavailable(fake, error: Exception) -> None:
    fake(error)
    with pytest.raises(ModelUnavailable) as caught:
        llm.ask_llm("s", "c", REVIEW_REPLY_SCHEMA)
    assert caught.value.__cause__ is None


@pytest.mark.parametrize(
    "result",
    [
        response(refusal=True),
        response(status="incomplete", incomplete=SimpleNamespace(reason="max_output_tokens")),
        response(text=""),
    ],
)
def test_refusal_incomplete_or_empty_become_model_reply_invalid(fake, result: Any) -> None:
    fake(result)
    with pytest.raises(ModelReplyInvalid):
        llm.ask_llm("s", "c", REVIEW_REPLY_SCHEMA)


def test_client_has_timeout_and_no_retries() -> None:
    client = llm.get_client()
    assert client.max_retries == 0
    assert client.timeout == llm.TIMEOUT_SECONDS
