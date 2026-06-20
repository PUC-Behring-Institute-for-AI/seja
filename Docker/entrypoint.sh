#!/usr/bin/env bash
set -euo pipefail

if [ -f /root/.seja/.env ]; then
    set -a
    source /root/.seja/.env
    set +a
fi

SEJA_DB_PATH="${SEJA_DB_PATH:-/root/.seja-state/seja.db}"

if [ "${SEJA_RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    python -m seja_mcp.db.migrate
fi

echo "Starting SEJA-MCP server..."
python -m seja_mcp.server &
MCP_PID=$!

echo "Waiting for MCP health endpoint..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8765/health > /dev/null 2>&1; then
        echo "MCP server is healthy"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: MCP server failed to start within 30s"
        exit 1
    fi
    sleep 1
done

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

exec "$@"
