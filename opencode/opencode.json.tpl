{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode-go/deepseek-v4-pro",
  "small_model": "opencode-go/deepseek-v4-flash",
  "mcp_servers": [
    {
      "name": "seja",
      "type": "streamable-http",
      "url": "http://localhost:8765/mcp",
      "enabled": true
    }
  ],
  "agent": {
    "seja-strategy": {
      "model": "opencode-go/deepseek-v4-pro",
      "mode": "primary",
      "groups": ["seja"],
      "mcp_servers": ["seja"]
    },
    "seja-architect": {
      "model": "opencode-go/deepseek-v4-pro",
      "mode": "primary",
      "groups": ["seja"],
      "mcp_servers": ["seja"]
    },
    "seja-planner": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "primary",
      "groups": ["seja"],
      "mcp_servers": ["seja"]
    },
    "seja-implement": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "primary",
      "groups": ["seja"],
      "mcp_servers": ["seja"]
    },
    "seja-check": {
      "model": "opencode-go/deepseek-v4-pro",
      "mode": "primary",
      "groups": ["seja"],
      "mcp_servers": ["seja"]
    },
    "seja-triage": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-oracle": {
      "model": "opencode-go/deepseek-v4-pro",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-research": {
      "model": "opencode-go/deepseek-v4-pro",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-council": {
      "model": "opencode-go/deepseek-v4-pro",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-semiotic": {
      "model": "opencode-go/deepseek-v4-pro",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-tester": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-docs": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-brief": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-workspace": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-boost": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    },
    "seja-chronicler": {
      "model": "opencode-go/deepseek-v4-flash",
      "mode": "hidden",
      "mcp_servers": ["seja"]
    }
  },
  "customCommands": [
    {
      "name": "seja-plan",
      "description": "Create or review execution plans",
      "command": "seja-plan"
    },
    {
      "name": "seja-check",
      "description": "Quality verification — modes: review, health, telemetry, semiotic",
      "command": "seja-check"
    },
    {
      "name": "seja-debug",
      "description": "Deep problem investigation",
      "command": "seja-debug"
    },
    {
      "name": "seja-docs",
      "description": "Generate technical documentation",
      "command": "seja-docs"
    },
    {
      "name": "seja-triage",
      "description": "Classify and route incoming requests",
      "command": "seja-triage"
    },
    {
      "name": "seja-research",
      "description": "Investigate technologies or solutions",
      "command": "seja-research"
    },
    {
      "name": "seja-council",
      "description": "Multi-perspective decision evaluation",
      "command": "seja-council"
    },
    {
      "name": "seja-semiotic",
      "description": "Evaluate semiotic coherence of the system",
      "command": "seja-semiotic"
    },
    {
      "name": "seja-brief",
      "description": "Generate context summary for session handover",
      "command": "seja-brief"
    },
    {
      "name": "seja-boost",
      "description": "Identify and apply performance optimizations",
      "command": "seja-boost"
    },
    {
      "name": "seja-workspace",
      "description": "Manage workspaces and worktrees",
      "command": "seja-workspace"
    },
    {
      "name": "seja-status",
      "description": "Report project state — lifecycle phase, pending items, health",
      "command": "seja-status"
    },
    {
      "name": "seja-inspect",
      "description": "Deep inspection of system state, decisions, or plans",
      "command": "seja-inspect"
    }
  ],
  "agentGroups": {
    "seja": {
      "agents": [
        "seja-strategy",
        "seja-architect",
        "seja-planner",
        "seja-implement",
        "seja-check"
      ]
    }
  },
  "env": {
    "SEJA_MCP_URL": "http://localhost:8765/mcp",
    "SEJA_WORKSPACE_DIR": "/workspace"
  },
  "plugins": [
    {
      "name": "@whisperopencode/push",
      "enabled": false
    },
    {
      "name": "@tarquinen/opencode-dcp",
      "enabled": false
    },
    {
      "name": "opencode-notify",
      "enabled": false
    },
    {
      "name": "@slkiser/opencode-quota",
      "enabled": false
    }
  ],
  "providers": [
    {
      "name": "opencode"
    },
    {
      "name": "opencode-go"
    },
    {
      "name": "openrouter"
    },
    {
      "name": "nvidia"
    }
  ],
  "contextWindowLimits": {
    "seja-strategy": 64000,
    "seja-architect": 64000,
    "seja-oracle": 96000,
    "seja-council": 128000,
    "seja-semiotic": 64000,
    "seja-research": 64000,
    "seja-check": 64000,
    "seja-planner": 48000,
    "seja-implement": 48000,
    "seja-triage": 24000,
    "seja-tester": 24000,
    "seja-docs": 32000,
    "seja-brief": 32000,
    "seja-workspace": 24000,
    "seja-boost": 24000,
    "seja-chronicler": 32000
  },
  "toolUsePolicies": {
    "seja-triage": {
      "bash": false,
      "write": false,
      "edit": false
    },
    "seja-oracle": {
      "bash": false,
      "write": false,
      "edit": false
    },
    "seja-council": {
      "bash": false,
      "write": false,
      "edit": false
    },
    "seja-semiotic": {
      "bash": false,
      "write": false,
      "edit": false
    },
    "seja-brief": {
      "bash": false,
      "write": false,
      "edit": false
    },
    "seja-chronicler": {
      "bash": false,
      "write": false,
      "edit": false
    }
  }
}
