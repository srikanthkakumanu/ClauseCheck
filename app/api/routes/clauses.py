"""POST /clauses/review."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.schemas import ErrorResponse, ReviewRequest, ReviewResponse
from app.application.review_clause import ReviewClause

router = APIRouter(prefix="/clauses", tags=["clauses"])


def get_review_clause(request: Request) -> ReviewClause:
    """The use case wired by app.main.create_app()."""
    return request.app.state.review_clause


@router.post(
    "/review",
    response_model=ReviewResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def review_clause(
    body: ReviewRequest, use_case: Annotated[ReviewClause, Depends(get_review_clause)]
) -> ReviewResponse:
    """Screen one clause: a risk level, a summary and up to 5 grounded issues."""
    return ReviewResponse.from_result(use_case.execute(body.clause))
