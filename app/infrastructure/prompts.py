"""Loads prompts from the prompts/ directory. Prompts never live inline in code."""

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@lru_cache(maxsize=8)
def load_prompt(name: str) -> str:
    """Return the text of prompts/<name>.md."""
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
