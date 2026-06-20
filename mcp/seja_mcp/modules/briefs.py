from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.db.schema import ensure_schema
from seja_mcp.modules import dual_write

def register_tools(mcp):

    @mcp.tool
    @dual_write()
    async def log_started(workspace_path: str, phase: str, content: str, session_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            brief_id = str(uuid7())
            await db.execute(
                "INSERT INTO briefs (id, project_id, phase, content, session_id, status) "
                "VALUES (?, ?, ?, ?, ?, 'started')",
                (brief_id, pid, phase, content, session_id),
            )
            await db.commit()

        return {"status": "created", "brief_id": brief_id}


    @mcp.tool
    @dual_write()
    async def log_done(workspace_path: str, brief_id: str, conclusion: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT b.* FROM briefs b "
                "JOIN projects p ON b.project_id = p.id "
                "WHERE p.workspace_path = ? AND b.id = ?",
                (workspace_path, brief_id),
            )
            if not cursor:
                return {"status": "not_found"}
            if cursor[0]["status"] != "started":
                return {"status": "error", "error": "Brief already completed"}

            existing = cursor[0]["content"]
            updated = f"{existing}\n\n## Conclusion\n\n{conclusion}"
            await db.execute(
                "UPDATE briefs SET content = ?, status = 'done' WHERE id = ?",
                (updated, brief_id),
            )
            await db.commit()

        return {"status": "completed", "brief_id": brief_id}


    @mcp.tool
    async def get_recent_briefs(workspace_path: str, limit: int = 5) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT b.* FROM briefs b "
                "JOIN projects p ON b.project_id = p.id "
                "WHERE p.workspace_path = ? "
                "ORDER BY b.created_at DESC LIMIT ?",
                (workspace_path, limit),
            )
            return {"status": "ok", "briefs": [dict(r) for r in cursor]}

