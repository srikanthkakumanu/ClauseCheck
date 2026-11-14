
# PROJECT.md — ClauseCheck

## Purpose

A small API that screens one contract clause and flags risky wording, so a legal-ops team
can triage incoming contracts faster. One request, one LLM call, one JSON answer.
It triages; a lawyer decides.

## Success looks like

- A clause of 20 to 4000 characters in; a risk level, a summary and up to 5 issues out, or a clean error.
- Every issue quotes the clause. A quote that is not in the submitted text is rejected, never returned.
- The whole test suite runs offline, with no API key.

## In scope

- POST /clauses/review.

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

- prompts/review.md — the system prompt
- src/llm.py — the only file that talks to the model
- src/schemas.py — request and reply validation
- src/routes/clauses.py — the request flow, including the grounding check
