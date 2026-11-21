"""Settings, read once from the process environment.

Never reads a .env file itself: scripts/start.sh (or `set -a; . ./.env; set +a`) supplies the
environment, so tests never see real keys.
"""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ReasoningEffort = Literal["none", "low", "medium", "high"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
LogFormat = Literal["json", "console"]


class Settings(BaseSettings):
    """All configuration for ClauseCheck."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore", case_sensitive=False)

    openai_api_key: SecretStr = Field(min_length=1)
    clausecheck_model: str = Field(min_length=1)
    clausecheck_reasoning_effort: ReasoningEffort = "low"

    log_level: LogLevel = "INFO"
    log_format: LogFormat = "json"

    langsmith_tracing: bool = False
    langsmith_hide_inputs: bool = False
    langsmith_hide_outputs: bool = False

    @field_validator(
        "clausecheck_model",
        "clausecheck_reasoning_effort",
        "log_format",
        "langsmith_tracing",
        "langsmith_hide_inputs",
        "langsmith_hide_outputs",
        mode="before",
    )
    @classmethod
    def _strip_lower(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("log_level", mode="before")
    @classmethod
    def _strip_upper(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _tracing_hides_text(self) -> Self:
        if self.langsmith_tracing and not (
            self.langsmith_hide_inputs and self.langsmith_hide_outputs
        ):
            raise ValueError(
                "LANGSMITH_TRACING=true requires LANGSMITH_HIDE_INPUTS=true and "
                "LANGSMITH_HIDE_OUTPUTS=true: clause text must never be sent"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings for this process, built on first use."""
    return Settings()  # type: ignore[call-arg]  # values come from the environment
