#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/backend/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

exec "$PYTHON" "$SCRIPT_DIR/push.py" "$@"
