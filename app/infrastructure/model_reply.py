"""Anti-corruption layer: turns the model's raw JSON reply into a domain Review.

The model's reply is untrusted. It is parsed with strict pydantic models and then built into
domain objects. Errors are re-raised as ModelReplyInvalid without chaining, because pydantic
error messages quote the input they rejected.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.application.errors import ModelReplyInvalid
from app.domain.errors import InvalidReview
from app.domain.review import (
    MAX_CONCERN_LENGTH,
    MAX_ISSUES,
    MAX_SUMMARY_LENGTH,
    Issue,
    Review,
    RiskLevel,
)

SCHEMA_NAME = "clause_review"

# Sent to the model as a strict JSON schema (Structured Outputs). Kept to keywords strict mode
# accepts; length and count limits are enforced by the pydantic models below.
REVIEW_REPLY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["risk", "summary", "issues"],
    "properties": {
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "summary": {
            "type": "string",
            "description": f"One or two sentences, at most {MAX_SUMMARY_LENGTH} characters.",
        },
        "issues": {
            "type": "array",
            "description": f"At most {MAX_ISSUES} issues.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["excerpt", "concern"],
                "properties": {
                    "excerpt": {
                        "type": "string",
                        "description": "Copied verbatim from the clause.",
                    },
                    "concern": {
                        "type": "string",
                        "description": f"At most {MAX_CONCERN_LENGTH} characters.",
                    },
                },
            },
        },
    },
}


class _IssueReply(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    excerpt: str
    concern: str = Field(min_length=1, max_length=MAX_CONCERN_LENGTH)


class _ReviewReply(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    risk: Literal["low", "medium", "high"]
    summary: str = Field(min_length=1, max_length=MAX_SUMMARY_LENGTH)
    issues: list[_IssueReply] = Field(max_length=MAX_ISSUES)


def parse_review_reply(text: str) -> Review:
    """Parse the model's JSON reply into a Review, or raise ModelReplyInvalid."""
    try:
        reply = _ReviewReply.model_validate_json(text)
    except ValidationError:
        raise ModelReplyInvalid("model reply did not match the expected schema") from None
    try:
        return Review(
            risk=RiskLevel(reply.risk),
            summary=reply.summary,
            issues=tuple(Issue(excerpt=i.excerpt, concern=i.concern) for i in reply.issues),
        )
    except InvalidReview:
        raise ModelReplyInvalid("model reply broke a review rule") from None
