# ClauseCheck

A small API that screens one contract clause for risky wording. It returns a triage risk level,
a short summary and the exact phrases that raised concern. It triages; a lawyer still decides.

- One endpoint: `POST /clauses/review`
- One LLM call per request, made through the OpenAI SDK
- Clause text is never stored or logged: clauses are confidential

## Quick start

Requires [uv](https://docs.astral.sh/uv/). It uses Python 3.15 (pinned in `.python-version`) and installs it if missing.

```sh
uv sync                                   # install dependencies
cp .env.example .env                      # then fill in OPENAI_API_KEY and CLAUSECHECK_MODEL
scripts/start.sh                          # starts on http://127.0.0.1:8000
scripts/stop.sh                           # stops it
```

`scripts/start.sh` loads `.env` if it exists (it is gitignored; `.env.example` is the template). Use a different port with
`PORT=4000 scripts/start.sh`. The server runs in the background; its PID is kept in
`.run/clausecheck.pid` and its logs (stdout, JSON or console per `LOG_FORMAT`) in `.run/clausecheck.log`.

Interactive API docs are at `/docs` while the server is running.

## Example

Request (made-up clause):

```sh
curl -s http://127.0.0.1:8000/clauses/review \
  -H 'Content-Type: application/json' \
  -d '{"clause": "The Supplier may terminate this Agreement at any time without notice and retain all fees paid."}'
```

Response:

```json
{
  "risk": "high",
  "summary": "One-sided termination right with no notice and no refund.",
  "issues": [
    {
      "excerpt": "terminate this Agreement at any time without notice",
      "concern": "The supplier can end the contract immediately, leaving no time to find a replacement."
    },
    {
      "excerpt": "retain all fees paid",
      "concern": "Prepaid fees are kept even if no service is delivered."
    }
  ],
  "disclaimer": "Automated triage only. This is not legal advice; a lawyer must review the clause."
}
```

## Contract

| Field | Rule |
|---|---|
| `clause` (request) | string, 20–4000 characters |
| `risk` | `low`, `medium` or `high` |
| `summary` | short text |
| `issues` | 0–5 items of `{excerpt, concern}`; every `excerpt` is quoted exactly from the clause |
| `disclaimer` | always present, added by the server |

## Errors

| Status | `error` | When |
|---|---|---|
| 400 | `invalid_clause` | missing field, wrong type, or clause outside 20–4000 characters |
| 502 | `model_unavailable` | the LLM call failed |
| 502 | `model_reply_invalid` | the model's reply did not match the expected shape |
| 502 | `ungrounded_issue` | the model quoted text that is not in the clause |

Error bodies look like `{"error": "invalid_clause", "detail": "clause must be 20-4000 characters"}`.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | yes | API key for the LLM provider. Environment only, never committed. |
| `CLAUSECHECK_MODEL` | yes | Model name. No default. Use `gpt-6-luna` locally, `gpt-6.1-terra` in production. |
| `CLAUSECHECK_REASONING_EFFORT` | no | Model reasoning effort: `none`, `low`, `medium` or `high`. Default `low`. |
| `PORT` | no | Port for `scripts/start.sh`. Default `8000`. |
| `LOG_LEVEL` | no | `DEBUG`, `INFO`, `WARNING` or `ERROR`. Default `INFO`. |
| `LOG_FORMAT` | no | `json` (default, for Fly.io) or `console` (readable, for local dev). |
| `LANGSMITH_TRACING` | no | `true` sends traces to LangSmith. Default off. |
| `LANGSMITH_API_KEY` | if tracing | LangSmith API key. Environment only, never committed. |
| `LANGSMITH_ENDPOINT` | if tracing | `https://api.smith.langchain.com` |
| `LANGSMITH_PROJECT` | if tracing | `ClauseCheck` |
| `LANGSMITH_HIDE_INPUTS` | if tracing | Must be `true`: clause text is never sent. |
| `LANGSMITH_HIDE_OUTPUTS` | if tracing | Must be `true`: model replies are never sent. |

### Logging

JSON lines to stdout via structlog; on Fly.io read them with `fly logs`. Each request gets a
`request_id`, returned in the `X-Request-ID` response header, which also appears in every log
line for that request. Logs hold only metadata (status, latency, risk level, issue count, error
code); clause text and model replies are never logged. See
[ARCHITECTURE.md](ARCHITECTURE.md#9-logging).

### Tracing with LangSmith

Optional. Traces carry metadata only: model name, latency, token counts, risk level, issue count,
grounding result and error code. Clause text, prompts and model replies are never sent; see
[ARCHITECTURE.md](ARCHITECTURE.md#10-tracing-with-langsmith). The app refuses to start with
tracing on unless both hide flags are `true`.

## Development

```sh
uv run pytest                 # full suite, offline, no API key needed
uv run ruff check
uv run ruff format --check
```

Tests never call the real model: `ask_llm` is patched or a fake is injected.

## Run in a container

```sh
docker build -t clausecheck .
docker run --rm --env-file .env -p 4000:8080 clausecheck   # http://127.0.0.1:4000
```

The container always listens on 8080. Keep `.env` comments on their own lines and values without
trailing spaces: `--env-file` reads each line literally.

## Deploy to Fly.io

```sh
fly launch --no-deploy                                   # once: creates the app from fly.toml
fly secrets set OPENAI_API_KEY=... LANGSMITH_API_KEY=...  # secrets never go in fly.toml
fly deploy
fly logs
```

Non-secret settings (model, log level, LangSmith flags) live in `fly.toml` under `[env]`.
See [ARCHITECTURE.md](ARCHITECTURE.md#11-containerization-and-deployment).

## Project layout

```
app/
  api/             HTTP routes, DTOs, error mapping
  application/     the ReviewClause use case
  domain/          Clause, Issue, RiskLevel, Review, grounding rule
  infrastructure/  config, LLM client, prompt loading, reply parsing
  main.py          wires it all together
prompts/review.md  the system prompt
scripts/           start.sh, stop.sh
Dockerfile         container image
fly.toml           Fly.io config
tests/             mirrors app/
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the layers, diagrams and testing strategy, and
[PROJECT.md](PROJECT.md) for scope and what is deliberately left out.

## Not in scope

Whole-document upload, storing clauses or results, "safe"/"unsafe" verdicts or legal advice,
caller accounts, and rewriting clauses.
