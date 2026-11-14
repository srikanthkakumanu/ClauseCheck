# Claude.md - ClauseCheck

## Project Context

@PROJECT.md

## Architecture

- FastAPI REST API, Python, Pydantic, typing, pytest, uv modules.
- No Database.
- One LLM call per request.
- Strictly layered architecture and domain driven design.
- Deployed as a single container on Fly.io.

## LLM Usage

- Only src/llm.py may import OpenAI SDK. Everything else calls askLLM().
- The model name comes from CLAUSECHECK_MODEL in .env. Never hardcode it.
- The prompt lives in prompts/review.md, never inline in code.
- Never trust model's reply. Validate it with the pydantic schema in src/schemas.py, then check every issue's exerpt appears in the submitted clause. Anything else: 502.
- The disclaimer field is added by server, never by model.

## Conventions

- Tests: Pytest. Run with `uv run pytest`. Always mock src/llm.py: tests must never call the real API or need a key.
- New endpoints go in src/routes/, one file per resource.
- Commits: Conventional Commits.

## Do Not

- Do not log or store contract text or raw model replies. Clauses are confidential.
- Do not label a clause "safe" or give legal advice. Risk is low, medium or high; nothing more.
- Do not commit API keys. OpenAI SDK API Key comes from the environment only.
- Do not add accounts or document upload.

## Working Files

- if TASK.md exists, read it first and tick items off as you finish them.
