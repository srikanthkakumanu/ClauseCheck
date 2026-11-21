
# TASK.md — POST /clauses/review

- [X] Docs: README.md, ARCHITECTURE.md with diagrams, CLAUDE.md/PROJECT.md updated
- [ ] pyproject.toml + uv.lock + .python-version 3.15, requires-python ">=3.15" (fastapi, uvicorn, openai, pydantic-settings, langsmith, structlog; dev: pytest, ruff; ruff line-length 100, target py315 or the newest ruff supports) — verify: uv sync installs every dependency on 3.15
- [ ] prompts/review.md
- [ ] domain: Clause, Issue, RiskLevel, Review, grounding rule, errors + tests
- [ ] infrastructure: config, ask_llm() (Responses API, strict JSON schema, reasoning effort, no temperature), prompt loader, reply parser, ReviewModel adapter + tests
- [ ] application: ReviewClause use case + ReviewModel port, adds disclaimer + tests
- [ ] api: routes/clauses.py, schemas, 400/502 error mapping, main.py wiring + tests
- [X] .env.example with LLM, server, logging and LangSmith variables
- [ ] scripts/start.sh and scripts/stop.sh (PID in .run/, PORT env, loads .env)
- [ ] Logging: infrastructure/logging.py (structlog, JSON/console, allowlist, show_locals=False), api/middleware.py (request_id, access line) + no-leak log tests
- [ ] LangSmith tracing in infrastructure: wrap_openai, metadata only, hide flags enforced at startup + no-leak test
- [ ] Dockerfile (multi-stage, pinned, non-root, 8080), .dockerignore, fly.toml (TCP check, [env]) — verify: docker build
- [ ] verify: pytest, ruff check, ruff format --check
- [ ] I try one real call with a sample clause, then we handle whatever the real reply looks like
- [ ] I deploy: fly launch, fly secrets set, fly deploy

Delete this file when the work is merged.
