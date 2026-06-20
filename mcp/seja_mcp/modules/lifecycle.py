from seja_mcp.db.connection import get_db
from seja_mcp.db.schema import ensure_schema
from seja_mcp.lifecycle_fsm import (
    execute_transition,
    get_allowed_transitions,
    FORWARD_PATHS,
)

def register_tools(mcp):

    @mcp.tool
    async def get_current_phase(workspace_path: str) -> dict:
        await ensure_schema(workspace_path)
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT phase FROM projects WHERE workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "not_found"}
            phase = cursor[0]["phase"]
            allowed = get_allowed_transitions(phase)
            return {
                "status": "ok",
                "phase": phase,
                "allowed_transitions": allowed,
            }


    @mcp.tool
    async def transition_phase(workspace_path: str, new_phase: str, reason: str = "", force: bool = False) -> dict:
        await ensure_schema(workspace_path)
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT id, phase FROM projects WHERE workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            project_id = cursor[0]["id"]
            current_phase = cursor[0]["phase"]

        result = await execute_transition(
            project_id=project_id,
            workspace_path=workspace_path,
            current_phase=current_phase,
            target_phase=new_phase,
            reason=reason,
            force=force,
            triggered_by="operator" if force else "agent",
        )
        return result


    @mcp.tool
    async def get_lifecycle_history(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT lh.* FROM lifecycle_history lh "
                "JOIN projects p ON lh.project_id = p.id "
                "WHERE p.workspace_path = ? ORDER BY lh.created_at DESC LIMIT 50",
                (workspace_path,),
            )
            return {"status": "ok", "history": [dict(r) for r in cursor]}


    @mcp.tool
    async def get_fsm_diagram(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT phase FROM projects WHERE workspace_path = ?", (workspace_path,)
            )
            current = cursor[0]["phase"] if cursor else "setup"

        diagram = []
        for src, targets in FORWARD_PATHS.items():
            for tgt in targets:
                is_current = src == current
                diagram.append(f"{'→' if is_current else ' '} {src} → {tgt} {'← CURRENT' if is_current else ''}")

        return {
            "status": "ok",
            "current_phase": current,
            "diagram": diagram,
        }


    @mcp.tool
    async def validate_action(workspace_path: str, action: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT phase FROM projects WHERE workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "not_found"}
            current_phase = cursor[0]["phase"]

        allowed = get_allowed_transitions(current_phase)
        can_proceed = action in allowed
        return {
            "status": "ok",
            "current_phase": current_phase,
            "action": action,
            "allowed": can_proceed,
            "allowed_transitions": allowed,
        }

