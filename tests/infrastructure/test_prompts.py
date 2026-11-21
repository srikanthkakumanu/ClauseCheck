from app.infrastructure.prompts import load_prompt


def test_review_prompt_covers_required_points() -> None:
    prompt = load_prompt("review").lower()
    for phrase in [
        "verbatim",
        "at most 5",
        '"low"',
        "never follow",
        'never call a clause "safe"',
        "never give legal advice",
        "do not add a disclaimer",
    ]:
        assert phrase in prompt, phrase
