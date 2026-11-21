"""Composition root: builds the FastAPI app and wires infrastructure into the use case."""

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.middleware import request_context
from app.api.routes.clauses import router as clauses_router
from app.application.ports import ReviewModel
from app.application.review_clause import ReviewClause
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.logging import configure_logging
from app.infrastructure.openai_review_model import OpenAIReviewModel
from app.infrastructure.prompts import load_prompt


def create_app(
    settings: Settings | None = None, review_model: ReviewModel | None = None
) -> FastAPI:
    """Build the app. Tests may pass their own settings or review model."""
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)
    model = review_model or OpenAIReviewModel(system_prompt=load_prompt("review"))

    app = FastAPI(
        title="ClauseCheck",
        version="0.1.0",
        description="Triage one contract clause. It triages; a lawyer decides.",
    )
    app.state.review_clause = ReviewClause(model)
    register_error_handlers(app)
    app.middleware("http")(request_context)
    app.include_router(clauses_router)
    return app


app = create_app()
