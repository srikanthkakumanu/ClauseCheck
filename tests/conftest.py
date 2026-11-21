"""Shared fixtures. Tests run offline: dummy key, dummy model, tracing forced off.

The environment is set before app modules are imported, so a real .env or exported shell
variables can never leak into tests.
"""

import json
import os

for _name in list(os.environ):
    if _name.startswith(("LANGSMITH_", "LANGCHAIN_", "OPENAI_", "CLAUSECHECK_", "LOG_")):
        del os.environ[_name]
os.environ.update(
    {
        "OPENAI_API_KEY": "test-key-not-real",
        "CLAUSECHECK_MODEL": "test-model",
        "LANGSMITH_TRACING": "false",
        "LOG_FORMAT": "json",
        "LOG_LEVEL": "INFO",
    }
)

from collections.abc import Callable, Iterator  # noqa: E402

import pytest  # noqa: E402

from app.infrastructure.config import get_settings  # noqa: E402
from app.infrastructure.llm import get_client  # noqa: E402

CLAUSE = (
    "The Supplier may terminate this Agreement at any time without notice and retain all fees paid."
)
SECRET_MARKER = "ZEBRA-7731"
"""A word placed in clause text so tests can prove it never reaches logs or traces."""

CLAUSE_WITH_MARKER = f"{CLAUSE} Code word {SECRET_MARKER} applies to all renewals."


def reply_json(
    risk: str = "high",
    summary: str = "One-sided termination right with no notice and no refund.",
    issues: list[dict[str, str]] | None = None,
) -> str:
    """A model reply as JSON text."""
    if issues is None:
        issues = [
            {
                "excerpt": "terminate this Agreement at any time without notice",
                "concern": "The supplier can end the contract immediately.",
            },
            {"excerpt": "retain all fees paid", "concern": "Prepaid fees are kept."},
        ]
    return json.dumps({"risk": risk, "summary": summary, "issues": issues})


@pytest.fixture(autouse=True)
def _fresh_caches() -> Iterator[None]:
    get_settings.cache_clear()
    get_client.cache_clear()
    yield
    get_settings.cache_clear()
    get_client.cache_clear()


@pytest.fixture
def make_reply() -> Callable[..., str]:
    return reply_json
