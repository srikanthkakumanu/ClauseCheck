"""Ports the use case depends on. Infrastructure provides the implementations."""

from typing import Protocol

from app.domain.clause import Clause
from app.domain.review import Review


class ReviewModel(Protocol):
    """Reviews one clause.

    Raises app.application.errors.ModelUnavailable or ModelReplyInvalid on failure.
    """

    def review(self, clause: Clause) -> Review: ...
