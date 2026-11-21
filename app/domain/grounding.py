"""The grounding rule: every issue must quote the clause exactly."""

from app.domain.clause import Clause
from app.domain.errors import UngroundedIssue
from app.domain.review import Review


def check_grounded(review: Review, clause: Clause) -> None:
    """Raise UngroundedIssue unless every excerpt is an exact substring of the clause."""
    for position, issue in enumerate(review.issues, start=1):
        if issue.excerpt not in clause.text:
            raise UngroundedIssue(f"issue {position} quotes text that is not in the clause")
