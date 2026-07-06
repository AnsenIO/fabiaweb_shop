#!/usr/bin/env bash
set -euo pipefail

# Start the fabiaweb_shop server (Flask -> gunicorn, loopback only).
# Usage: ./start.sh [PORT]

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8080}"

# Activate local virtualenv if it exists
if [ -f "${APP_DIR}/.venv/bin/activate" ]; then
    # shellcheck source=/dev/null
    source "${APP_DIR}/.venv/bin/activate"
fi

cd "${APP_DIR}"

exec gunicorn \
    --bind "127.0.0.1:${PORT}" \
    --workers 2 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile - \
    server:app
