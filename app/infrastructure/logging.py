"""structlog setup: JSON (or console) lines to stdout, metadata fields only.

Two guards keep clause text out of logs:
- every key not in ALLOWED_FIELDS is dropped just before rendering;
- exceptions are reduced to their type and file:line frames, never their message or locals.
"""

import logging
import sys
import traceback
from types import TracebackType

import structlog
from structlog.types import EventDict, Processor, WrappedLogger

ALLOWED_FIELDS = frozenset(
    {
        "timestamp",
        "level",
        "event",
        "logger",
        "request_id",
        "method",
        "path",
        "status",
        "latency_ms",
        "clause_length",
        "risk",
        "issue_count",
        "grounded",
        "error",
        "model",
        "tokens_in",
        "tokens_out",
        "exception_type",
        "stack",
    }
)
MAX_STACK_FRAMES = 15

ExcInfo = tuple[type[BaseException], BaseException, TracebackType | None]


def _to_exc_info(value: object) -> ExcInfo | None:
    if value is True:
        info = sys.exc_info()
        return info if info[0] is not None else None  # type: ignore[return-value]
    if isinstance(value, BaseException):
        return (type(value), value, value.__traceback__)
    if isinstance(value, tuple) and len(value) == 3 and value[0] is not None:
        return value  # type: ignore[return-value]
    return None


def reduce_exception(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Replace exc_info with exception_type and frames; drop any rendered exception text."""
    info = _to_exc_info(event_dict.pop("exc_info", None))
    event_dict.pop("exception", None)
    event_dict.pop("stack_info", None)
    if info is not None:
        exc_type, _exc, tb = info
        event_dict["exception_type"] = exc_type.__name__
        frames = traceback.extract_tb(tb)[-MAX_STACK_FRAMES:]
        event_dict["stack"] = [f"{f.filename}:{f.lineno} in {f.name}" for f in frames]
    return event_dict


def allowlist_fields(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Drop every key that is not explicitly allowed."""
    return {key: value for key, value in event_dict.items() if key in ALLOWED_FIELDS}


class _StdoutHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Writes to whatever sys.stdout is at emit time, so reassigned streams are respected."""

    def __init__(self) -> None:
        super().__init__(sys.stdout)

    @property  # type: ignore[override]
    def stream(self) -> object:
        return sys.stdout

    @stream.setter
    def stream(self, _value: object) -> None:
        pass


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    """Route structlog and stdlib (incl. uvicorn) logs through one pipeline to stdout."""
    shared: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    renderer: Processor = (
        structlog.processors.JSONRenderer()
        if fmt == "json"
        else structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            reduce_exception,
            allowlist_fields,
            renderer,
        ],
    )
    handler = _StdoutHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True
    # The request middleware writes the access line; uvicorn's would add the client IP.
    access = logging.getLogger("uvicorn.access")
    access.handlers = []
    access.propagate = False
    access.disabled = True
