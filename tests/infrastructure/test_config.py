import pytest
from pydantic import ValidationError

from app.infrastructure.config import Settings


def test_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUSECHECK_MODEL", "  gpt-6-luna ")
    monkeypatch.setenv("CLAUSECHECK_REASONING_EFFORT", "Medium")
    settings = Settings()
    assert settings.clausecheck_model == "gpt-6-luna"
    assert settings.clausecheck_reasoning_effort == "medium"
    assert settings.log_format == "json"


def test_missing_model_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUSECHECK_MODEL")
    with pytest.raises(ValidationError, match="clausecheck_model"):
        Settings()


def test_missing_api_key_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(ValidationError, match="openai_api_key"):
        Settings()


def test_never_reads_dotenv_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("CLAUSECHECK_MODEL=from-dotenv\n")
    monkeypatch.chdir(tmp_path)
    assert Settings().clausecheck_model == "test-model"


@pytest.mark.parametrize(
    ("hide_inputs", "hide_outputs"),
    [(None, None), ("true", None), (None, "true"), ("false", "true")],
)
def test_tracing_requires_both_hide_flags(
    monkeypatch: pytest.MonkeyPatch, hide_inputs: str | None, hide_outputs: str | None
) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    for name, value in (
        ("LANGSMITH_HIDE_INPUTS", hide_inputs),
        ("LANGSMITH_HIDE_OUTPUTS", hide_outputs),
    ):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError, match="clause text must never be sent"):
        Settings()


def test_tracing_with_hide_flags_tolerates_spaces_and_case(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_HIDE_INPUTS", "TRUE   ")
    monkeypatch.setenv("LANGSMITH_HIDE_OUTPUTS", " true")
    assert Settings().langsmith_tracing is True


def test_api_key_is_not_in_repr() -> None:
    assert "test-key-not-real" not in repr(Settings())
