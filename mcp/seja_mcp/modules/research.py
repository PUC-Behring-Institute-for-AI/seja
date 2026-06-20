from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.db.schema import ensure_schema
from seja_mcp.modules import dual_write

def register_tools(mcp):

    @mcp.tool
    @dual_write()
    async def create_research(workspace_path: str, question: str, findings: str, sources: str = "", recommendation: str = "") -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            report_id = str(uuid7())
            await db.execute(
                "INSERT INTO research_reports (id, project_id, question, findings, sources, recommendation) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (report_id, pid, question, findings, sources, recommendation or None),
            )
            await db.commit()

        return {"status": "created", "report_id": report_id}


    @mcp.tool
    async def get_research(workspace_path: str, report_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT r.* FROM research_reports r "
                "JOIN projects p ON r.project_id = p.id "
                "WHERE p.workspace_path = ? AND r.id = ?",
                (workspace_path, report_id),
            )
            if not cursor:
                return {"status": "not_found"}
            return {"status": "ok", "report": dict(cursor[0])}


    @mcp.tool
    async def list_research(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT r.id, r.question, r.recommendation, r.created_at FROM research_reports r "
                "JOIN projects p ON r.project_id = p.id "
                "WHERE p.workspace_path = ? ORDER BY r.created_at DESC",
                (workspace_path,),
            )
            return {"status": "ok", "reports": [dict(r) for r in cursor]}

