"""The ReviewClause use case: one clause in, one grounded review plus disclaimer out."""

from dataclasses import dataclass

import structlog

from app.application.errors import ModelError
from app.application.ports import ReviewModel
from app.domain.clause import Clause
from app.domain.errors import UngroundedIssue
from app.domain.grounding import check_grounded
from app.domain.review import Review

DISCLAIMER = "Automated triage only. This is not legal advice; a lawyer must review the clause."

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ReviewResult:
    """A grounded review with the server-added disclaimer."""

    review: Review
    disclaimer: str


class ReviewClause:
    """Validate the clause, ask the model, enforce grounding, add the disclaimer."""

    def __init__(self, model: ReviewModel) -> None:
        self._model = model

    def execute(self, text: str) -> ReviewResult:
        clause = Clause(text)
        try:
            review = self._model.review(clause)
        except ModelError as exc:
            log.warning("review.failed", error=exc.code, clause_length=len(text))
            raise
        try:
            check_grounded(review, clause)
        except UngroundedIssue as exc:
            log.warning(
                "review.failed",
                error=exc.code,
                grounded=False,
                issue_count=len(review.issues),
                clause_length=len(text),
            )
            raise
        log.info(
            "review.completed",
            risk=review.risk.value,
            issue_count=len(review.issues),
            grounded=True,
            clause_length=len(text),
        )
        return ReviewResult(review=review, disclaimer=DISCLAIMER)
