"""Domain errors. Messages are fixed strings and never contain clause or reply text."""


class DomainError(Exception):
    """Base class for rule violations in the domain."""

    code: str = "domain_error"


class InvalidClause(DomainError):
    """The submitted clause breaks a Clause invariant."""

    code = "invalid_clause"


class InvalidReview(DomainError):
    """A review or issue breaks a Review/Issue invariant."""

    code = "invalid_review"


class UngroundedIssue(DomainError):
    """An issue excerpt does not appear in the clause."""

    code = "ungrounded_issue"
