"""Per-request context: a request_id on every log line and one access line per request."""

import re
import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")

log = structlog.get_logger(__name__)


def resolve_request_id(header_value: str | None) -> str:
    """Reuse the caller's id only if it is short and safe; otherwise make a new one."""
    if header_value and _VALID_REQUEST_ID.fullmatch(header_value):
        return header_value
    return uuid.uuid4().hex


async def request_context(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Bind request_id, return it as a header, and log method/path/status/latency only."""
    request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception(
            "request.failed",
            method=request.method,
            path=request.url.path,
            status=500,
            latency_ms=_elapsed_ms(started),
        )
        raise
    response.headers[REQUEST_ID_HEADER] = request_id
    log.info(
        "request.completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=_elapsed_ms(started),
    )
    return response


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)
