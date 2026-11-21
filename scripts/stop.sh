#!/bin/sh
# Stop ClauseCheck started by scripts/start.sh. Safe to run when it is not running.
set -eu
cd "$(dirname "$0")/.."

PID_FILE=.run/clausecheck.pid

if [ ! -f "$PID_FILE" ]; then
    echo "ClauseCheck is not running."
    exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    i=0
    while kill -0 "$PID" 2>/dev/null && [ "$i" -lt 10 ]; do
        sleep 1
        i=$((i + 1))
    done
    if kill -0 "$PID" 2>/dev/null; then
        echo "ClauseCheck did not stop within 10 s; forcing." >&2
        kill -9 "$PID"
    fi
    echo "ClauseCheck stopped (PID $PID)."
else
    echo "ClauseCheck was not running (stale PID file removed)."
fi
rm -f "$PID_FILE"
