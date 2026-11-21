"""Request and response DTOs. The request DTO checks shape only; Clause owns the rules."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictStr

from app.application.review_clause import ReviewResult


class ReviewRequest(BaseModel):
    """POST /clauses/review body."""

    model_config = ConfigDict(extra="forbid")

    clause: StrictStr


class IssueOut(BaseModel):
    """One issue: an excerpt quoted from the clause and the concern it raises."""

    excerpt: str
    concern: str


class ReviewResponse(BaseModel):
    """A triage result. Every excerpt appears verbatim in the submitted clause."""

    risk: Literal["low", "medium", "high"]
    summary: str
    issues: list[IssueOut]
    disclaimer: str

    @classmethod
    def from_result(cls, result: ReviewResult) -> ReviewResponse:
        review = result.review
        return cls(
            risk=review.risk.value,
            summary=review.summary,
            issues=[IssueOut(excerpt=i.excerpt, concern=i.concern) for i in review.issues],
            disclaimer=result.disclaimer,
        )


class ErrorResponse(BaseModel):
    """Error body. `detail` never echoes the clause or the model reply."""

    error: str
    detail: str
