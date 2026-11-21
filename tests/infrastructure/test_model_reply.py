import json

import pytest

from app.application.errors import ModelReplyInvalid
from app.domain.review import RiskLevel
from app.infrastructure.model_reply import REVIEW_REPLY_SCHEMA, parse_review_reply
from tests.conftest import SECRET_MARKER, reply_json


def test_valid_reply_becomes_review() -> None:
    review = parse_review_reply(reply_json())
    assert review.risk is RiskLevel.HIGH
    assert len(review.issues) == 2


@pytest.mark.parametrize(
    "text",
    [
        "not json at all",
        json.dumps({"risk": "high", "summary": "Risky."}),  # missing issues
        json.dumps({"risk": "safe", "summary": "Fine.", "issues": []}),  # verdict, not a risk
        json.dumps({"risk": "high", "summary": "Risky.", "issues": [], "verdict": "unsafe"}),
        reply_json(summary="x" * 501),
        reply_json(issues=[{"excerpt": "abc def", "concern": "x" * 301}]),
        reply_json(issues=[{"excerpt": "abc def", "concern": "c"}] * 6),
        reply_json(issues=[{"excerpt": "ab", "concern": "too short excerpt"}]),
        json.dumps({"risk": "high", "summary": 5, "issues": []}),
    ],
)
def test_bad_replies_raise_model_reply_invalid(text: str) -> None:
    with pytest.raises(ModelReplyInvalid):
        parse_review_reply(text)


def test_error_never_quotes_the_reply() -> None:
    with pytest.raises(ModelReplyInvalid) as caught:
        parse_review_reply(reply_json(summary=SECRET_MARKER * 100))
    assert SECRET_MARKER not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True


def test_schema_is_strict_compatible() -> None:
    def check(node: dict) -> None:
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
            for child in node["properties"].values():
                check(child)
        if node.get("type") == "array":
            check(node["items"])

    check(REVIEW_REPLY_SCHEMA)
