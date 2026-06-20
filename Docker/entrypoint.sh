#!/usr/bin/env bash
set -euo pipefail

if [ -f /root/.seja/.env ]; then
    set -a
    source /root/.seja/.env
    set +a
fi

SEJA_DB_PATH="${SEJA_DB_PATH:-/root/.seja-state/seja.db}"

# ── Preflight: migrations + templates (before MCP) ──────────
if [ "${SEJA_RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    python -m seja_mcp.db.migrate
fi

echo "Rendering agent templates..."
for tpl in /root/.config/opencode/agents/*.md.tpl; do
    [ -f "$tpl" ] || continue
    envsubst '${SEJA_TIER_REASON} ${SEJA_TIER_CODE} ${SEJA_TIER_FAST}' \
        < "$tpl" > "${tpl%.tpl}"
done

echo "Validating rendered templates..."
if grep -rl '\${SEJA_TIER_' /root/.config/opencode/agents/*.md 2>/dev/null; then
    echo "ERROR: Unrendered template variables found in agent files"
    exit 1
fi

git config --global core.hooksPath /dev/null

# ── Foreground: MCP server as PID 1 ─────────────────────────
echo "Starting SEJA-MCP server..."
exec python -m seja_mcp.server
