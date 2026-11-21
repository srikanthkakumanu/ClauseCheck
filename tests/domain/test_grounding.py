import pytest

from app.domain.clause import Clause
from app.domain.errors import UngroundedIssue
from app.domain.grounding import check_grounded
from app.domain.review import Issue, Review, RiskLevel

CLAUSE = Clause("The Supplier may terminate this Agreement at any time without notice.")


def review_with(*excerpts: str) -> Review:
    issues = tuple(Issue(excerpt=e, concern="Concern.") for e in excerpts)
    return Review(risk=RiskLevel.HIGH, summary="Risky.", issues=issues)


def test_grounded_excerpts_pass() -> None:
    check_grounded(review_with("at any time without notice", "The Supplier"), CLAUSE)


def test_no_issues_is_grounded() -> None:
    check_grounded(review_with(), CLAUSE)


@pytest.mark.parametrize(
    "excerpt",
    [
        "without any notice",  # paraphrase
        "WITHOUT NOTICE",  # case differs
        "at any time  without notice",  # whitespace differs
        "terminate ... notice",  # ellipsis
    ],
)
def test_ungrounded_excerpt_raises(excerpt: str) -> None:
    with pytest.raises(UngroundedIssue) as caught:
        check_grounded(review_with("The Supplier", excerpt), CLAUSE)
    assert "issue 2" in str(caught.value)
    assert excerpt not in str(caught.value)
