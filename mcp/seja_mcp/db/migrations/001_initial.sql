-- Migration 001: Initial schema
-- Applied by schema.py ensure_schema() on first run

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    workspace_path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT 'setup',
    last_export_attempt TEXT,
    last_export_success TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS constitution_principles (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    principle TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    context TEXT NOT NULL,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'accepted',
    supersedes TEXT,
    superseded_by TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS decisions_fts USING fts5(
    id UNINDEXED, title, context, decision, rationale,
    content=decisions, content_rowid=rowid
);

CREATE TRIGGER IF NOT EXISTS decisions_ai AFTER INSERT ON decisions BEGIN
    INSERT INTO decisions_fts(rowid, id, title, context, decision, rationale)
    VALUES (new.rowid, new.id, new.title, new.context, new.decision, new.rationale);
END;

CREATE TRIGGER IF NOT EXISTS decisions_ad AFTER DELETE ON decisions BEGIN
    INSERT INTO decisions_fts(decisions_fts, rowid, id, title, context, decision, rationale)
    VALUES ('delete', old.rowid, old.id, old.title, old.context, old.decision, old.rationale);
END;

CREATE TRIGGER IF NOT EXISTS decisions_au AFTER UPDATE ON decisions BEGIN
    INSERT INTO decisions_fts(decisions_fts, rowid, id, title, context, decision, rationale)
    VALUES ('delete', old.rowid, old.id, old.title, old.context, old.decision, old.rationale);
    INSERT INTO decisions_fts(rowid, id, title, context, decision, rationale)
    VALUES (new.rowid, new.id, new.title, new.context, new.decision, new.rationale);
END;

CREATE TABLE IF NOT EXISTS design_features (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    feature_id TEXT NOT NULL,
    as_intended TEXT NOT NULL,
    as_coded TEXT,
    metacomm_type TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_id, feature_id)
);

CREATE TABLE IF NOT EXISTS lifecycle_history (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    from_phase TEXT NOT NULL,
    to_phase TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    transition_type TEXT NOT NULL DEFAULT 'forward',
    triggered_by TEXT NOT NULL DEFAULT 'agent',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pending_actions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_required TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS briefs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase TEXT NOT NULL,
    content TEXT NOT NULL,
    session_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'started',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS telemetry (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase TEXT NOT NULL,
    agent TEXT NOT NULL,
    skill TEXT NOT NULL,
    action TEXT NOT NULL,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'success',
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS telemetry_config (
    project_id TEXT PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
    retention_days INTEGER NOT NULL DEFAULT 90
);

CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    goal TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    approved_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS plan_steps (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    checker TEXT,
    checker_done_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS research_reports (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    findings TEXT NOT NULL,
    sources TEXT NOT NULL DEFAULT '',
    recommendation TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS perspective_definitions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    depth INTEGER NOT NULL DEFAULT 0,
    questions TEXT NOT NULL DEFAULT '[]',
    depth_factor INTEGER NOT NULL DEFAULT 1,
    agent_assignment TEXT
);

CREATE TABLE IF NOT EXISTS journey_maps (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    feature_id TEXT NOT NULL,
    jm_tb TEXT NOT NULL,
    jm_e TEXT,
    journey_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS test_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    plan_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    result TEXT NOT NULL DEFAULT 'pending',
    total INTEGER NOT NULL DEFAULT 0,
    passed INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0,
    details TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL UNIQUE,
    branch TEXT NOT NULL,
    worktree_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'forked',
    semiotic_score REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS export_log (
    id TEXT PRIMARY KEY,
    workspace_path TEXT NOT NULL,
    module TEXT NOT NULL,
    file_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'success',
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
