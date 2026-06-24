#!/usr/bin/env bash
set -euo pipefail

if [ -f /root/.seja/.env ]; then
    set -a
    source /root/.seja/.env
    set +a
fi

SEJA_DB_PATH="${SEJA_DB_PATH:-/root/.seja-state/seja.db}"

# ── Render opencode.json from template ──
if [ -f /root/.config/opencode/opencode.json.tpl ]; then
    cp /root/.config/opencode/opencode.json.tpl /root/.config/opencode/opencode.json
    echo "Generated opencode.json from template"
fi

# ── Migrations (before MCP, MCP needs DB) ──
if [ "${SEJA_RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    python -m seja_mcp.db.migrate
fi

# ── Render agent templates ──
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

# Garantir que AGENTS.md global esteja no lugar esperado
if [ -f /root/.config/opencode/AGENTS.md.global ]; then
    cp /root/.config/opencode/AGENTS.md.global /root/.config/opencode/AGENTS.md
fi

git config --global core.hooksPath /dev/null

# ── Start MCP server in background ──
echo "Starting MCP server in background..."
python -m seja_mcp.server &
MCP_PID=$!

# ── Wait for MCP to become healthy ──
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

# ── Start OpenCode in foreground ──
echo "Starting OpenCode server (headless)..."
exec oc serve --port 4096 --hostname 0.0.0.0 --print-logs
