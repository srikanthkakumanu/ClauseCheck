"""The only module that talks to the OpenAI SDK.

ask_llm() makes exactly one Responses API call with Structured Outputs: no retries, a 30 s
timeout, no temperature, and store=False so OpenAI does not keep the clause.
"""

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import structlog
from openai import OpenAI, OpenAIError

from app.application.errors import ModelReplyInvalid, ModelUnavailable
from app.infrastructure.config import get_settings

TIMEOUT_SECONDS = 30.0

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class LlmReply:
    """The model's reply text plus metadata that is safe to log."""

    text: str
    model: str
    tokens_in: int | None
    tokens_out: int | None

    def __repr__(self) -> str:
        return f"LlmReply(model={self.model}, length={len(self.text)})"


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """One OpenAI client per process, wrapped for LangSmith when tracing is on."""
    settings = get_settings()
    client = OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
    )
    if settings.langsmith_tracing:
        from langsmith.wrappers import wrap_openai

        client = wrap_openai(client)
    return client


def ask_llm(
    system_prompt: str, user_text: str, json_schema: dict[str, Any], schema_name: str = "reply"
) -> LlmReply:
    """Send one request and return the reply text.

    Raises ModelUnavailable if the call fails, ModelReplyInvalid if the model refuses or the
    response is incomplete.
    """
    settings = get_settings()
    started = time.perf_counter()
    try:
        response = get_client().responses.create(
            model=settings.clausecheck_model,
            instructions=system_prompt,
            input=user_text,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": json_schema,
                    "strict": True,
                }
            },
            reasoning={"effort": settings.clausecheck_reasoning_effort},
            store=False,
        )
    except OpenAIError as exc:
        log.warning(
            "llm.call_failed",
            error=ModelUnavailable.code,
            exception_type=type(exc).__name__,
            model=settings.clausecheck_model,
            latency_ms=_elapsed_ms(started),
        )
        raise ModelUnavailable("the model call failed") from None

    usage = response.usage
    tokens_in = usage.input_tokens if usage else None
    tokens_out = usage.output_tokens if usage else None
    log.info(
        "llm.call_completed",
        model=settings.clausecheck_model,
        latency_ms=_elapsed_ms(started),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )

    if response.status != "completed" or response.incomplete_details is not None:
        raise ModelReplyInvalid("the model response was incomplete")
    for item in response.output:
        if item.type == "message" and any(part.type == "refusal" for part in item.content):
            raise ModelReplyInvalid("the model refused to review the clause")
    text = response.output_text
    if not text:
        raise ModelReplyInvalid("the model reply was empty")
    return LlmReply(
        text=text, model=settings.clausecheck_model, tokens_in=tokens_in, tokens_out=tokens_out
    )


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)
