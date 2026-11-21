"""Maps domain and application errors to HTTP status codes and error bodies."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.errors import ModelError, ModelReplyInvalid, ModelUnavailable
from app.domain.errors import DomainError, InvalidClause, UngroundedIssue

STATUS_BY_ERROR: dict[type[Exception], int] = {
    InvalidClause: 400,
    UngroundedIssue: 502,
    ModelUnavailable: 502,
    ModelReplyInvalid: 502,
}

REQUEST_SHAPE_DETAIL = "request body must be JSON with one string field 'clause'"


def _body(code: str, detail: str) -> dict[str, str]:
    return {"error": code, "detail": detail}


async def _request_validation_handler(_: Request, __: Exception) -> JSONResponse:
    # Never return exc.errors(): it contains the submitted input.
    return JSONResponse(status_code=400, content=_body(InvalidClause.code, REQUEST_SHAPE_DETAIL))


async def _app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError | ModelError)
    status = STATUS_BY_ERROR.get(type(exc), 502)
    # Messages of these errors are fixed strings that never contain clause or reply text.
    return JSONResponse(status_code=status, content=_body(exc.code, str(exc)))


def register_error_handlers(app: FastAPI) -> None:
    """Replace FastAPI's 422 with 400 and map ClauseCheck errors to 400/502."""
    app.add_exception_handler(RequestValidationError, _request_validation_handler)
    app.add_exception_handler(DomainError, _app_error_handler)
    app.add_exception_handler(ModelError, _app_error_handler)
