"""Review, Issue and RiskLevel: the triage result for one clause."""

from dataclasses import dataclass
from enum import StrEnum

from app.domain.errors import InvalidReview

MAX_ISSUES = 5
MIN_EXCERPT_CHARS = 3
MAX_CONCERN_LENGTH = 300
MAX_SUMMARY_LENGTH = 500


class RiskLevel(StrEnum):
    """Overall triage level. Never "safe": only a lawyer can say that."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class Issue:
    """One risky phrase: an excerpt quoted from the clause and why it is a concern."""

    excerpt: str
    concern: str

    def __post_init__(self) -> None:
        if len(self.excerpt.strip()) < MIN_EXCERPT_CHARS:
            raise InvalidReview(f"excerpt must have at least {MIN_EXCERPT_CHARS} characters")
        if not 1 <= len(self.concern) <= MAX_CONCERN_LENGTH or not self.concern.strip():
            raise InvalidReview(f"concern must be 1-{MAX_CONCERN_LENGTH} characters")

    def __repr__(self) -> str:
        return f"Issue(excerpt_length={len(self.excerpt)})"


@dataclass(frozen=True, slots=True)
class Review:
    """A risk level, a short summary and 0-5 issues."""

    risk: RiskLevel
    summary: str
    issues: tuple[Issue, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.risk, RiskLevel):
            raise InvalidReview("risk must be low, medium or high")
        if not 1 <= len(self.summary) <= MAX_SUMMARY_LENGTH or not self.summary.strip():
            raise InvalidReview(f"summary must be 1-{MAX_SUMMARY_LENGTH} characters")
        if len(self.issues) > MAX_ISSUES:
            raise InvalidReview(f"a review has at most {MAX_ISSUES} issues")

    def __repr__(self) -> str:
        return f"Review(risk={self.risk.value}, issues={len(self.issues)})"
