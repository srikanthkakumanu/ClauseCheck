
# PROJECT.md — ClauseCheck

## Purpose

A small API that screens one contract clause and flags risky wording, so a legal-ops team
can triage incoming contracts faster. One request, one LLM call, one JSON answer.
It triages; a lawyer decides.

## Success looks like

- A clause of 20 to 4000 characters in; a risk level, a summary and up to 5 issues out, or a clean error.
- Every issue quotes the clause. A quote that is not in the submitted text is rejected, never returned.
- The whole test suite runs offline, with no API key.
- Start and stop with one script each.
- One `docker build`, one `fly deploy`; no secrets in the image or in git.

## In scope

- POST /clauses/review.
- Optional LangSmith tracing, metadata only (no clause text).
- Structured JSON application logs (structlog), metadata only (no clause text).
- One container image (Dockerfile), deployed to Fly.io (fly.toml).

## Out of scope, and why

- Whole-document upload — long documents need chunking and a different design.
- Storing clauses or results — contract text is confidential, and we don't need it.
- A "safe" or "unsafe" verdict, or advice — only a lawyer can give those, so the API only triages.
- Accounts for callers — demo-scale; if it grows, add auth at the gateway, not in this service.
- Rewriting the clause — a different project with a different risk profile.

## Glossary

- "clause": the contract text submitted for review.
- "issue": one { excerpt, concern } pair. The excerpt is a quote from the clause.
- "risk": overall triage level, low, medium or high.
- "grounded": an issue whose excerpt really appears in the clause.

## Where things live

Layers and diagrams are in ARCHITECTURE.md.

- README.md — how to run, call and test the API
- ARCHITECTURE.md — layers, dependency rule, diagrams, testing strategy
- prompts/review.md — the system prompt
- app/main.py — composition root: builds the app and wires the layers
- app/api/ — HTTP: routes/clauses.py, request/response DTOs, error → 400/502 mapping
- app/application/review_clause.py — the review use case; adds the disclaimer
- app/domain/ — Clause, Issue, RiskLevel, Review; grounding.py holds the grounding check
- app/infrastructure/llm.py — the only file that talks to the model
- app/infrastructure/model_reply.py — validates the model's reply
- app/infrastructure/config.py — settings from the environment
- app/infrastructure/logging.py — structlog setup and log field allowlist
- app/api/middleware.py — request_id and access log per request
- .env.example — template for the gitignored .env
- scripts/start.sh, scripts/stop.sh — run and stop the server
- Dockerfile, .dockerignore, fly.toml — container image and Fly.io deployment
- tests/ — mirrors app/, one folder per layer
