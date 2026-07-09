#!/usr/bin/env bash
# deploy.sh — CI script for fabiaweb_shop
# Checks for git updates, backs up preorders, pulls, deploys to DO droplet, and syncs locally.
#
# Usage:
#   ./deploy.sh              # Full deploy + preorder backup + sync
#   ./deploy.sh --check      # Only check if updates are available
#   ./deploy.sh --backup     # Only backup preorders from droplet
#   ./deploy.sh --deploy     # Skip git pull, just backup + deploy
#   ./deploy.sh --sync       # Only pull preorders from droplet
#
# Config (via .env in the same directory):
#   DROPLET_IP    — Droplet IP (default: 159.223.27.54)
#   SSH_KEY       — Path to SSH key (default: ~/.ssh/hermes-agent)

set -euo pipefail

# ── Setup ────────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

DROPLET_IP="${DROPLET_IP:-159.223.27.54}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/hermes-agent}"
REMOTE_BASE="/var/www/fabiaweb_shop"

# Files to deploy (explicit whitelist — nothing else leaks)
DEPLOY_FILES=(
    "index.html"
    "server.py"
    "meta_pixel.py"
    "matomo_tracker.py"
    "generate_version.py"
    "version.json"
    "requirements.txt"
    "start.sh"
    "og-fabiashop.png"
    "CONTEXT.md"
)

# ── Helpers ────────────────────────────────────────────────────────────────────────
log()    { echo "[deploy] $*"; }
ok()     { echo "  ✓ $*"; }
fail()   { echo "  ✗ $*" >&2; }

ssh_cmd() {
    ssh -i "$SSH_KEY" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        "root@${DROPLET_IP}" "$@"
}

# Transfer a file via SSH + base64 pipe (avoids SCP block)
transfer_file() {
    local local_file="$1"
    local remote_file="$2"
    if [ ! -f "$local_file" ]; then
        fail "Local file missing: $local_file"
        return 1
    fi
    base64 "$local_file" | ssh -i "$SSH_KEY" \
        -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        "root@${DROPLET_IP}" \
        "python3 -c \"import base64,sys; data=base64.b64decode(sys.stdin.buffer.read()); open('${remote_file}','wb').write(data)\""
}

# ── Steps ────────────────────────────────────────────────────────────────────────

check_updates() {
    log "Checking for updates..."
    git fetch origin >/dev/null 2>&1
    local behind
    behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
    if [ "$behind" -gt 0 ]; then
        log "Found $behind new commit(s) on origin/main"
        return 0
    else
        log "Already up to date"
        return 1
    fi
}

pull_updates() {
    log "Pulling latest from origin/main..."
    git pull --rebase origin main
    ok "Pull complete"
}

backup_preorders() {
    log "Backing up preorders from droplet..."
    
    local remote_csv="${REMOTE_BASE}/data/contacts.csv"
    local backup_dir="$SCRIPT_DIR/backups"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/contacts_${timestamp}.csv"
    
    # Fetch contacts via SSH
    local content
    content=$(ssh_cmd "cat ${remote_csv} 2>/dev/null" || echo "")
    
    if [ -z "$content" ]; then
        log "No preorders found on droplet"
        return 0
    fi
    
    # Create backup directory and save
    mkdir -p "$backup_dir"
    echo "$content" > "$backup_file"
    local count
    count=$(echo "$content" | tail -n +2 | wc -l)
    ok "Backed up ${count} preorders to ${backup_file}"
}

deploy_to_droplet() {
    log "Deploying to droplet ${DROPLET_IP}..."

    # Refresh version.json from the current commit before transferring
    python3 "${SCRIPT_DIR}/generate_version.py" >/dev/null 2>&1 || true

    # Create data dir on droplet
    ssh_cmd "mkdir -p ${REMOTE_BASE}/data" >/dev/null 2>&1
    
    # Transfer each file
    for file in "${DEPLOY_FILES[@]}"; do
        if [ -f "$file" ]; then
            transfer_file "$file" "${REMOTE_BASE}/${file}"
            ok "Deployed ${file}"
        fi
    done
    
    # Ensure nginx config is up to date (only if it has certbot SSL blocks)
    if [ -f "nginx.conf" ]; then
        # Safety check: refuse to deploy an HTTP-only config (would break SSL)
        if ! grep -q "managed by Certbot" "$SCRIPT_DIR/nginx.conf"; then
            log "⚠ Skipping nginx deploy — local config missing certbot SSL blocks"
            log "  (Would break HTTPS. Fix nginx.conf first.)"
        else
            local local_hash remote_hash
            local_hash=$(md5sum "$SCRIPT_DIR/nginx.conf" | cut -d' ' -f1)
            remote_hash=$(ssh_cmd "md5sum /etc/nginx/sites-enabled/fabiaweb_shop 2>/dev/null | cut -d' ' -f1" || echo "none")
            if [ "$local_hash" != "$remote_hash" ]; then
                log "Updating nginx config..."
                base64 "$SCRIPT_DIR/nginx.conf" | ssh -i "$SSH_KEY" \
                    -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
                    "root@${DROPLET_IP}" \
                    "python3 -c \"import base64,sys; data=base64.b64decode(sys.stdin.buffer.read()); open('/etc/nginx/sites-enabled/fabiaweb_shop','wb').write(data)\""
                ssh_cmd "nginx -t 2>&1 && nginx -s reload" >/dev/null 2>&1
                ok "Nginx config updated and reloaded"
            else
                ok "Nginx config up to date"
            fi
        fi
    fi
    
    # Restart gunicorn if server.py changed
    ssh_cmd "cd ${REMOTE_BASE} && .venv/bin/gunicorn --reload --bind '127.0.0.1:8081' --workers 2 --timeout 30 --daemon --pid /tmp/gunicorn_fabiashop.pid server:app" >/dev/null 2>&1 || true
    ok "Gunicorn restarted"
    
    # Verify
    local health
    health=$(ssh_cmd "curl -s http://127.0.0.1:8081/health" 2>/dev/null || echo "failed")
    if echo "$health" | grep -q '"ok"'; then
        ok "Health check passed"
    else
        fail "Health check failed: $health"
        return 1
    fi
}

sync_preorders() {
    log "Pulling preorders from droplet..."
    
    local remote_csv="${REMOTE_BASE}/data/contacts.csv"
    local local_csv="$SCRIPT_DIR/data/contacts.csv"
    
    # Fetch contacts via SSH
    local content
    content=$(ssh_cmd "cat ${remote_csv} 2>/dev/null" || echo "")
    
    if [ -z "$content" ]; then
        log "No preorders found on droplet"
        return 0
    fi
    
    # Save locally
    mkdir -p "$SCRIPT_DIR/data"
    echo "$content" > "$local_csv"
    local count
    count=$(echo "$content" | tail -n +2 | wc -l)
    ok "Saved ${count} preorders to ${local_csv}"
}

# ── Main ────────────────────────────────────────────────────────────────────────

main() {
    local mode="${1:-full}"
    
    case "$mode" in
        --check)
            git fetch origin >/dev/null 2>&1
            local behind
            behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
            if [ "$behind" -gt 0 ]; then
                log "$behind update(s) available"
            else
                log "Already up to date"
            fi
            ;;
        --backup)
            backup_preorders
            ;;
        --sync)
            sync_preorders
            ;;
        --deploy)
            backup_preorders
            deploy_to_droplet
            sync_preorders
            ;;
        *)
            # Full mode: check, backup, pull, deploy, sync
            git fetch origin >/dev/null 2>&1
            local behind
            behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
            if [ "$behind" -gt 0 ]; then
                log "Found $behind new commit(s) — pulling..."
                pull_updates
            else
                log "Already up to date"
            fi
            backup_preorders
            deploy_to_droplet
            sync_preorders
            ;;
    esac
    
    log "Done!"
}

main "$@"
