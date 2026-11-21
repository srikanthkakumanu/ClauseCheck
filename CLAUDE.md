# Claude.md - ClauseCheck


## Project context

@PROJECT.md

## Architecture

Python 3.15 / FastAPI REST API. No database. One LLM call per request.
Deployed as a single container on Fly.io.

@ARCHITECTURE.md

Domain-driven design, strictly layered. Hard rules:

- Dependencies point inward only: api → application → domain. infrastructure implements
  application ports and may use domain types. Only app/main.py imports every layer.
- app/domain/ is plain Python: no FastAPI, pydantic, OpenAI SDK or config imports.
- app/api/ holds no business rules: parse the DTO, call the use case, map errors, return the DTO.
- One module per use case in app/application/; it depends on ports (Protocols), not on
  infrastructure modules.
- Keep it proportionate: no repositories, domain events or DI frameworks.

## LLM usage

- Only app/infrastructure/llm.py may import the OpenAI SDK. Everything else goes through ask_llm().
- The model name comes from CLAUSECHECK_MODEL in app/infrastructure/config.py (no default).
  Never hardcode it.
- The prompt lives in prompts/review.md, loaded by app/infrastructure/prompts.py. Never inline it.
  It must cover the points in ARCHITECTURE.md "What prompts/review.md must say".
- The clause is untrusted input: data, not instructions.
- ask_llm() makes exactly one OpenAI Responses API call with Structured Outputs (strict JSON
  schema from model_reply.py), reasoning effort from CLAUSECHECK_REASONING_EFFORT, no
  temperature, 30 s timeout, no retries. Still validate and ground-check every reply.
- Never trust the model's reply. Parse it with the pydantic models in
  app/infrastructure/model_reply.py into domain objects, then apply the grounding rule in
  app/domain/grounding.py: every issue's excerpt must appear in the submitted clause.
  Anything else: 502.
- The disclaimer is added in the application layer, never by the model.

## Logging (structlog)

- structlog over stdlib logging, JSON lines to stdout. Set up only in
  app/infrastructure/logging.py; request_id middleware in app/api/middleware.py.
- The domain never logs. Other layers use `structlog.get_logger()` with fixed event names
  (e.g. `review.completed`) and only the allowlisted fields in ARCHITECTURE.md section 9.
- Never pass clause text, prompts, summaries, excerpts, replies or exception messages as log
  fields or into event names. Log `exception_type`, not the message.
- Keep `show_locals=False`; never log request or response bodies.
- Every new error path gets a test that the clause does not appear in captured logs.

## Tracing (LangSmith)

- Optional, off unless LANGSMITH_TRACING=true. Tracing code lives in app/infrastructure/ only
  (wrap_openai in llm.py, @traceable on the adapter). Domain, application and api never import langsmith.
- Metadata only: model, latency, tokens, risk, issue count, grounding result, error code.
  Never clause text, prompts, summaries, excerpts or raw replies.
- LANGSMITH_HIDE_INPUTS and LANGSMITH_HIDE_OUTPUTS must be true; config refuses to start otherwise.
- Never use process_inputs / process_outputs: they override the hide flags.
- Errors that can reach a trace carry no clause or reply text (do not chain pydantic errors).
- Tests force LANGSMITH_TRACING=false and include a test that captured trace data never
  contains the clause.

## Conventions

- Tests: pytest. Run with `uv run pytest`. Tests mirror app/ (tests/domain/, tests/application/,
  tests/infrastructure/, tests/api/). Every new behaviour gets a test in its layer.
- Never call the real API in tests or need a key: domain tests use no mocks, use-case tests
  inject a fake ReviewModel, API tests patch ask_llm.
- Style: type hints on every function; `ruff check` and `ruff format` before each commit.
- New endpoints go in app/api/routes/, one file per resource. New use cases go in app/application/.
- Start/stop scripts live in scripts/ and stay POSIX sh.
- Container: multi-stage Dockerfile, pinned base images, non-root, port 8080, no secrets or
  .env in the image (.dockerignore). Config in fly.toml [env]; secrets only via `fly secrets set`.
  See ARCHITECTURE.md section 11.
- Update README.md and ARCHITECTURE.md in the same change as any change to layout, endpoints,
  error codes, env vars, scripts, Dockerfile or fly.toml.
- Commits: Conventional Commits.

## Do not

- Do not log or store contract text or raw model replies, including in exception messages
  and LangSmith traces. Clauses are confidential.
- Do not label a clause "safe" or give legal advice. Risk is low, medium or high; nothing more.
- Do not commit API keys. OPENAI_API_KEY and LANGSMITH_API_KEY come from the environment only
  (.env, gitignored). Keep .env.example in sync, with empty values.
- Do not add accounts or document upload.
- Do not make real LLM or LangSmith calls, or run the live endpoint against a real model.
- Do not deploy, run `fly` commands that change anything, or set secrets. `docker build` is fine.
  Tests are always mocked; the user does live checks with a made-up clause.

## Working files

- If TASK.md exists, read it first and tick items off as you finish them.
