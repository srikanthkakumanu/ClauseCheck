#!/bin/sh
# Start ClauseCheck in the background.
#   - loads .env if it exists (gitignored; template: .env.example)
#   - listens on 127.0.0.1:${PORT:-8000}
#   - PID in .run/clausecheck.pid, logs in .run/clausecheck.log
set -eu
cd "$(dirname "$0")/.."

RUN_DIR=.run
PID_FILE="$RUN_DIR/clausecheck.pid"
LOG_FILE="$RUN_DIR/clausecheck.log"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "ClauseCheck is already running (PID $(cat "$PID_FILE"))." >&2
    exit 1
fi
rm -f "$PID_FILE"

if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi
PORT="${PORT:-8000}"
export PYTHONUNBUFFERED=1

uv sync --frozen --quiet
mkdir -p "$RUN_DIR"
nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --no-access-log \
    >>"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"

sleep 2
if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "ClauseCheck failed to start. Last log lines:" >&2
    tail -n 20 "$LOG_FILE" >&2
    exit 1
fi
echo "ClauseCheck running on http://127.0.0.1:$PORT (PID $(cat "$PID_FILE")). Logs: $LOG_FILE"
