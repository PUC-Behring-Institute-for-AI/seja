from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Project(BaseModel):
    id: str
    workspace_path: str
    name: str
    phase: str = "setup"
    last_export_attempt: Optional[str] = None
    last_export_success: Optional[str] = None
    version: int = 1
    created_at: str = ""
    updated_at: str = ""


class ConstitutionPrinciple(BaseModel):
    id: str
    project_id: str
    rank: int
    principle: str
    description: str
    created_at: str = ""


class Decision(BaseModel):
    id: str
    project_id: str
    title: str
    context: str
    decision: str
    rationale: str
    status: str = "accepted"
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    created_at: str = ""


class DesignFeature(BaseModel):
    id: str
    project_id: str
    feature_id: str
    as_intended: str
    as_coded: Optional[str] = None
    metacomm_type: str = ""
    status: str = "pending"
    created_at: str = ""


class LifecycleHistory(BaseModel):
    id: str
    project_id: str
    from_phase: str
    to_phase: str
    reason: str
    transition_type: str
    triggered_by: str = "agent"
    created_at: str = ""


class PendingAction(BaseModel):
    id: str
    project_id: str
    phase_required: str
    description: str
    status: str = "open"
    created_at: str = ""
    resolved_at: Optional[str] = None


class Brief(BaseModel):
    id: str
    project_id: str
    phase: str
    content: str
    session_id: str
    status: str = "started"
    created_at: str = ""


class Telemetry(BaseModel):
    id: str
    project_id: str
    phase: str
    agent: str
    skill: str
    action: str
    duration_ms: int = 0
    status: str = "success"
    error: Optional[str] = None
    created_at: str = ""


class TelemetryConfig(BaseModel):
    project_id: str
    retention_days: int = 90


class Plan(BaseModel):
    id: str
    project_id: str
    title: str
    goal: str
    status: str = "draft"
    approved_at: Optional[str] = None
    created_at: str = ""


class PlanStep(BaseModel):
    id: str
    plan_id: str
    step_number: int
    description: str
    checker: Optional[str] = None
    checker_done_at: Optional[str] = None
    status: str = "pending"
    created_at: str = ""


class ResearchReport(BaseModel):
    id: str
    project_id: str
    question: str
    findings: str
    sources: str
    recommendation: Optional[str] = None
    created_at: str = ""


class PerspectiveDefinition(BaseModel):
    id: str
    name: str
    depth: int
    questions: list[str]
    agent_assignment: Optional[str] = None


class JourneyMap(BaseModel):
    id: str
    project_id: str
    feature_id: str
    jm_tb: str
    jm_e: Optional[str] = None
    journey_type: str
    created_at: str = ""


class TestRun(BaseModel):
    id: str
    project_id: str
    plan_id: str
    scope: str
    result: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    details: str = ""
    created_at: str = ""


class Experiment(BaseModel):
    id: str
    project_id: str
    name: str
    branch: str
    worktree_path: str
    status: str = "forked"
    semiotic_score: Optional[float] = None
    created_at: str = ""


class ExportLog(BaseModel):
    id: str
    workspace_path: str
    module: str
    file_path: str
    sha256: str
    status: str = "success"
    error: Optional[str] = None
    created_at: str = ""
