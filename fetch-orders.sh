#!/bin/bash
# Download orders CSV from fabiaweb_shop droplet
# Usage: ./fetch-orders.sh [output-path]

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DROPLET_IP="${DROPLET_IP:-159.223.27.54}"
REMOTE_CSV="${REMOTE_CSV:-/var/www/fabiaweb_shop/data/orders.csv}"
OUTPUT="${1:-./orders.csv}"

echo "Fetching orders from $DROPLET_IP..."

scp -o StrictHostKeyChecking=no root@${DROPLET_IP}:${REMOTE_CSV} "${OUTPUT}"

if [ -f "${OUTPUT}" ]; then
    LINES=$(wc -l < "${OUTPUT}")
    echo "✓ Downloaded ${LINES} lines to ${OUTPUT}"
    echo ""
    echo "Preview:"
    head -5 "${OUTPUT}"
else
    echo "✗ Download failed"
    exit 1
fi
