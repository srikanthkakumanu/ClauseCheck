"""OpenAIReviewModel: the ReviewModel port implemented with ask_llm()."""

import structlog
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from app.domain.clause import Clause
from app.domain.review import Review
from app.infrastructure.llm import ask_llm
from app.infrastructure.model_reply import REVIEW_REPLY_SCHEMA, SCHEMA_NAME, parse_review_reply


class OpenAIReviewModel:
    """Reviews a clause with one LLM call and parses the reply into a domain Review."""

    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt

    @traceable(name="clause_review", run_type="chain")
    def review(self, clause: Clause) -> Review:
        # Inputs and outputs of this trace are hidden by LANGSMITH_HIDE_INPUTS/OUTPUTS
        # (enforced in config); only the metadata below is visible in LangSmith.
        reply = ask_llm(self._system_prompt, clause.text, REVIEW_REPLY_SCHEMA, SCHEMA_NAME)
        review = parse_review_reply(reply.text)
        run = get_current_run_tree()
        if run is not None:
            run.add_metadata(
                {
                    "request_id": structlog.contextvars.get_contextvars().get("request_id"),
                    "model": reply.model,
                    "tokens_in": reply.tokens_in,
                    "tokens_out": reply.tokens_out,
                    "risk": review.risk.value,
                    "issue_count": len(review.issues),
                }
            )
        return review
