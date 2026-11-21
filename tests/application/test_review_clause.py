import pytest

from app.application.errors import ModelReplyInvalid, ModelUnavailable
from app.application.review_clause import DISCLAIMER, ReviewClause
from app.domain.clause import Clause
from app.domain.errors import InvalidClause, UngroundedIssue
from app.domain.review import Issue, Review, RiskLevel
from tests.conftest import CLAUSE


class FakeModel:
    def __init__(self, result: Review | Exception) -> None:
        self.result = result
        self.calls: list[Clause] = []

    def review(self, clause: Clause) -> Review:
        self.calls.append(clause)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def grounded_review() -> Review:
    return Review(
        risk=RiskLevel.HIGH,
        summary="One-sided termination.",
        issues=(Issue(excerpt="retain all fees paid", concern="Fees are kept."),),
    )


def test_happy_path_adds_disclaimer() -> None:
    model = FakeModel(grounded_review())
    result = ReviewClause(model).execute(CLAUSE)
    assert result.disclaimer == DISCLAIMER
    assert result.review.risk is RiskLevel.HIGH
    assert len(model.calls) == 1


def test_invalid_clause_never_calls_model() -> None:
    model = FakeModel(grounded_review())
    with pytest.raises(InvalidClause):
        ReviewClause(model).execute("too short")
    assert model.calls == []


def test_ungrounded_excerpt_is_rejected() -> None:
    review = Review(
        risk=RiskLevel.HIGH,
        summary="Invented.",
        issues=(Issue(excerpt="unlimited liability", concern="Not in the clause."),),
    )
    with pytest.raises(UngroundedIssue):
        ReviewClause(FakeModel(review)).execute(CLAUSE)


@pytest.mark.parametrize("error", [ModelUnavailable("down"), ModelReplyInvalid("bad reply")])
def test_model_errors_propagate(error: Exception) -> None:
    with pytest.raises(type(error)):
        ReviewClause(FakeModel(error)).execute(CLAUSE)
