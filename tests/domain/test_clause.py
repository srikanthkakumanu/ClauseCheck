import pytest

from app.domain.clause import MAX_LENGTH, MIN_LENGTH, Clause
from app.domain.errors import InvalidClause


@pytest.mark.parametrize("length", [MIN_LENGTH, MAX_LENGTH])
def test_accepts_boundary_lengths(length: int) -> None:
    assert len(Clause("x" * length).text) == length


@pytest.mark.parametrize("length", [MIN_LENGTH - 1, MAX_LENGTH + 1, 0])
def test_rejects_out_of_range_lengths(length: int) -> None:
    with pytest.raises(InvalidClause, match="20-4000"):
        Clause("x" * length)


def test_rejects_whitespace_only() -> None:
    with pytest.raises(InvalidClause, match="blank"):
        Clause(" " * 30)


def test_counts_length_as_submitted_without_trimming() -> None:
    # 19 visible characters plus surrounding spaces still counts as 25.
    assert len(Clause("   " + "x" * 19 + "   ").text) == 25


def test_rejects_non_string() -> None:
    with pytest.raises(InvalidClause):
        Clause(12345)  # type: ignore[arg-type]


def test_repr_never_shows_text() -> None:
    assert "secret" not in repr(Clause("this is a secret clause text"))
