import pytest

from app.domain.errors import InvalidReview
from app.domain.review import Issue, Review, RiskLevel


def issue(excerpt: str = "without notice", concern: str = "No notice period.") -> Issue:
    return Issue(excerpt=excerpt, concern=concern)


def test_valid_review() -> None:
    review = Review(risk=RiskLevel.HIGH, summary="Risky.", issues=(issue(),))
    assert review.risk == "high"


def test_allows_zero_issues() -> None:
    assert Review(risk=RiskLevel.LOW, summary="Balanced.", issues=()).issues == ()


def test_rejects_more_than_five_issues() -> None:
    with pytest.raises(InvalidReview, match="at most 5"):
        Review(risk=RiskLevel.HIGH, summary="Risky.", issues=tuple(issue() for _ in range(6)))


def test_risk_has_no_safe_value() -> None:
    with pytest.raises(ValueError):
        RiskLevel("safe")


def test_rejects_non_enum_risk() -> None:
    with pytest.raises(InvalidReview):
        Review(risk="high", summary="Risky.", issues=())  # type: ignore[arg-type]


@pytest.mark.parametrize("summary", ["", "   ", "x" * 501])
def test_rejects_bad_summary(summary: str) -> None:
    with pytest.raises(InvalidReview, match="summary"):
        Review(risk=RiskLevel.LOW, summary=summary, issues=())


@pytest.mark.parametrize("excerpt", ["", "ab", "  a  "])
def test_rejects_short_excerpt(excerpt: str) -> None:
    with pytest.raises(InvalidReview, match="excerpt"):
        issue(excerpt=excerpt)


@pytest.mark.parametrize("concern", ["", "   ", "x" * 301])
def test_rejects_bad_concern(concern: str) -> None:
    with pytest.raises(InvalidReview, match="concern"):
        issue(concern=concern)
