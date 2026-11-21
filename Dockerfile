# syntax=docker/dockerfile:1
# ClauseCheck: multi-stage image. Build with uv, run on a slim, non-root runtime.

FROM ghcr.io/astral-sh/uv:0.13.9 AS uv

FROM python:3.15.2-slim AS build
# A C compiler for dependencies without prebuilt Python 3.15 wheels (e.g. zstandard).
# Build stage only: the runtime image gets the finished .venv, not the compiler.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.15.2-slim AS runtime
RUN useradd --create-home --uid 10001 clausecheck
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY app/ app/
COPY prompts/ prompts/
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_FORMAT=json
USER clausecheck
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
