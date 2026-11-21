"""The Clause value object: the contract text submitted for review."""

from dataclasses import dataclass

from app.domain.errors import InvalidClause

MIN_LENGTH = 20
MAX_LENGTH = 4000


@dataclass(frozen=True, slots=True)
class Clause:
    """Contract text of 20-4000 characters, counted as submitted (no trimming)."""

    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise InvalidClause("clause must be a string")
        if not MIN_LENGTH <= len(self.text) <= MAX_LENGTH:
            raise InvalidClause(f"clause must be {MIN_LENGTH}-{MAX_LENGTH} characters")
        if not self.text.strip():
            raise InvalidClause("clause must not be blank")

    def __repr__(self) -> str:
        # Never expose clause text through repr (logs, tracebacks, debuggers).
        return f"Clause(length={len(self.text)})"
