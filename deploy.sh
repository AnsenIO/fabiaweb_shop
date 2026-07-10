#!/usr/bin/env bash
# Thin wrapper — delegates to the unified deploy script.
# Run from either fabia_web/ or fabiaweb_shop/ — it finds the parent.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
# Go up one level to the unified deploy script
if [ -f "../deploy.sh" ]; then
    exec bash "../deploy.sh" "$@"
else
    echo "ERROR: ../deploy.sh not found. Copy this file there or run from the parent dir." >&2
    exit 1
fi
