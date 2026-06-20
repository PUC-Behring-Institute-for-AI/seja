from datetime import datetime

from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.modules import dual_write


def register_tools(mcp):

    @mcp.tool
    async def list_pending(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT pa.* FROM pending_actions pa "
                "JOIN projects p ON pa.project_id = p.id "
                "WHERE p.workspace_path = ? AND pa.status = 'open' ORDER BY pa.created_at",
                (workspace_path,),
            )
            return {"status": "ok", "pending": [dict(r) for r in cursor]}

    @mcp.tool
    @dual_write()
    async def add_pending(workspace_path: str, phase_required: str, description: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall("SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,))
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            action_id = str(uuid7())
            await db.execute(
                "INSERT INTO pending_actions (id, project_id, phase_required, description) VALUES (?, ?, ?, ?)",
                (action_id, pid, phase_required, description),
            )
            await db.commit()

        return {"status": "created", "pending_id": action_id}

    @mcp.tool
    @dual_write()
    async def resolve_pending(workspace_path: str, pending_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT pa.* FROM pending_actions pa "
                "JOIN projects p ON pa.project_id = p.id "
                "WHERE p.workspace_path = ? AND pa.id = ?",
                (workspace_path, pending_id),
            )
            if not cursor:
                return {"status": "not_found", "error": "Pending action not found"}
            if cursor[0]["status"] != "open":
                return {"status": "error", "error": "Pending action already resolved"}

            now = datetime.now().isoformat()
            await db.execute(
                "UPDATE pending_actions SET status = 'resolved', resolved_at = ? WHERE id = ?",
                (now, pending_id),
            )
            await db.commit()

        return {"status": "resolved", "pending_id": pending_id}

    @mcp.tool
    async def list_pending_blocking_transition(workspace_path: str, target_phase: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT pa.* FROM pending_actions pa "
                "JOIN projects p ON pa.project_id = p.id "
                "WHERE p.workspace_path = ? AND pa.phase_required = ? AND pa.status = 'open' "
                "ORDER BY pa.created_at",
                (workspace_path, target_phase),
            )
            return {
                "status": "ok",
                "blocking": [dict(r) for r in cursor],
                "count": len(cursor),
                "can_transition": len(cursor) == 0,
            }
