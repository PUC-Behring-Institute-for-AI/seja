from statemachine import StateMachine, State
import asyncio
from typing import Optional

from seja_mcp.db.connection import get_db

_LIFECYCLE_LOCK = asyncio.Lock()


class SejaLifecycleFSM(StateMachine):
    setup = State(initial=True)
    design = State()
    research = State()
    plan = State()
    implement = State()
    check = State()
    document = State()
    reflect = State()

    setup_to_design = setup.to(design, cond="constitution_not_empty")
    design_to_research = design.to(research, cond="design_intent_defined")
    research_to_plan = research.to(plan, cond="research_recommendation_clear")
    plan_to_implement = plan.to(implement, cond="plan_approved")
    implement_to_check = implement.to(check, cond="all_steps_done")
    check_to_document = check.to(document, cond="all_checks_passed")
    document_to_reflect = document.to(reflect, cond="documentation_generated")
    reflect_to_design = reflect.to(design)

    implement_to_design = implement.to(design, cond="reason_provided")
    implement_to_research = implement.to(research, cond="reason_provided")
    implement_to_plan = implement.to(plan, cond="reason_provided")
    plan_to_design = plan.to(design, cond="reason_provided")
    plan_to_research = plan.to(research, cond="reason_provided")
    design_to_setup = design.to(setup, cond="reason_provided")
    research_to_design = research.to(design, cond="reason_provided")
    research_to_setup = research.to(setup, cond="reason_provided")
    check_to_implement = check.to(implement, cond="reason_provided")
    check_to_plan = check.to(plan, cond="reason_provided")
    document_to_check = document.to(check, cond="reason_provided")

    context: Optional[dict] = None

    def constitution_not_empty(self):
        db = self.context["get_db"]
        pid = self.context["project_id"]
        cursor = db.execute(
            "SELECT COUNT(*) as cnt FROM constitution_principles WHERE project_id = ?",
            (pid,),
        )
        row = cursor.fetchone()
        return row["cnt"] > 0

    def design_intent_defined(self):
        db = self.context["get_db"]
        pid = self.context["project_id"]
        cursor = db.execute(
            "SELECT COUNT(*) as cnt FROM design_features WHERE project_id = ?",
            (pid,),
        )
        row = cursor.fetchone()
        return row["cnt"] > 0

    def research_recommendation_clear(self):
        db = self.context["get_db"]
        pid = self.context["project_id"]
        cursor = db.execute(
            "SELECT COUNT(*) as cnt FROM research_reports WHERE project_id = ? AND recommendation IS NOT NULL",
            (pid,),
        )
        row = cursor.fetchone()
        return row["cnt"] > 0

    def plan_approved(self):
        db = self.context["get_db"]
        pid = self.context["project_id"]
        cursor = db.execute(
            "SELECT COUNT(*) as cnt FROM plans WHERE project_id = ? AND status = 'approved'",
            (pid,),
        )
        row = cursor.fetchone()
        return row["cnt"] > 0

    def all_steps_done(self):
        db = self.context["get_db"]
        pid = self.context["project_id"]
        cursor = db.execute(
            "SELECT COUNT(*) as cnt FROM plan_steps ps "
            "JOIN plans p ON ps.plan_id = p.id "
            "WHERE p.project_id = ? AND p.status = 'approved' AND ps.status != 'done'",
            (pid,),
        )
        row = cursor.fetchone()
        return row["cnt"] == 0

    def all_checks_passed(self):
        db = self.context["get_db"]
        pid = self.context["project_id"]
        cursor = db.execute(
            "SELECT COUNT(*) as cnt FROM plan_steps ps "
            "JOIN plans p ON ps.plan_id = p.id "
            "WHERE p.project_id = ? AND p.status = 'approved' "
            "AND ps.checker IS NOT NULL AND ps.checker_done_at IS NULL",
            (pid,),
        )
        row = cursor.fetchone()
        return row["cnt"] == 0

    def documentation_generated(self):
        db = self.context["get_db"]
        pid = self.context["project_id"]
        cursor = db.execute(
            "SELECT COUNT(*) as cnt FROM journey_maps WHERE project_id = ?",
            (pid,),
        )
        row = cursor.fetchone()
        return row["cnt"] > 0

    def reason_provided(self):
        return bool(self.context.get("reason"))


FORWARD_PATHS: dict[str, list[str]] = {
    "setup": ["design"],
    "design": ["research", "setup"],
    "research": ["plan", "design", "setup"],
    "plan": ["implement", "design", "research"],
    "implement": ["check", "design", "research", "plan"],
    "check": ["document", "implement", "plan"],
    "document": ["reflect", "check"],
    "reflect": ["design"],
}


def get_allowed_transitions(current_phase: str) -> list[str]:
    return FORWARD_PATHS.get(current_phase, [])


async def execute_transition(
    project_id: str,
    workspace_path: str,
    current_phase: str,
    target_phase: str,
    reason: str = "",
    force: bool = False,
    triggered_by: str = "agent",
) -> dict:
    async with _LIFECYCLE_LOCK:
        async with get_db(workspace_path) as db:
            rv = {"success": False, "error": "", "from_phase": current_phase, "to_phase": target_phase}

            allowed = get_allowed_transitions(current_phase)
            if target_phase not in allowed and not force:
                rv["error"] = f"Transition from {current_phase} to {target_phase} not allowed"
                return rv

            if force and not reason:
                rv["error"] = "Force transition requires a reason"
                return rv

            if target_phase == current_phase:
                rv["error"] = "Already in target phase"
                return rv

            if not force and not reason and current_phase != "setup" and target_phase != allowed[0]:
                rv["error"] = f"Reverse transition from {current_phase} to {target_phase} requires a reason"
                return rv

            from uuid_extensions import uuid7

            history_id = str(uuid7())
            is_reverse = current_phase != "setup" and target_phase not in FORWARD_PATHS.get(current_phase, [])[:1]
            transition_type = "force" if force else ("reverse" if is_reverse else "forward")

            await db.execute(
                "INSERT INTO lifecycle_history (id, project_id, from_phase, to_phase, reason, transition_type, triggered_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (history_id, project_id, current_phase, target_phase, reason, transition_type, triggered_by),
            )

            await db.execute(
                "UPDATE projects SET phase = ?, version = version + 1, updated_at = datetime('now') WHERE id = ?",
                (target_phase, project_id),
            )

            await db.commit()

            from seja_mcp.sync.markdown_export import export_markdown_for
            await export_markdown_for(workspace_path)

            rv["success"] = True
            rv["history_id"] = history_id
            rv["transition_type"] = transition_type
            return rv
