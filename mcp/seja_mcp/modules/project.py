import os

from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.db.schema import ensure_schema, run_migrations
from seja_mcp.sync.markdown_export import export_all


def register_tools(mcp):

    @mcp.tool
    async def init_project(workspace_path: str, name: str) -> dict:
        await ensure_schema(workspace_path)
        await run_migrations(workspace_path)

        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT id, phase FROM projects WHERE workspace_path = ?", (workspace_path,)
            )
            if cursor:
                return {"status": "exists", "project_id": cursor[0]["id"], "phase": cursor[0]["phase"]}

            project_id = str(uuid7())
            await db.execute(
                "INSERT INTO projects (id, workspace_path, name) VALUES (?, ?, ?)",
                (project_id, workspace_path, name),
            )
            await db.commit()

        project_dir = os.path.join(workspace_path, ".seja")
        os.makedirs(os.path.join(project_dir, "decisions"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "plans"), exist_ok=True)

        await export_all(workspace_path)

        return {"status": "created", "project_id": project_id, "phase": "setup"}

    @mcp.tool
    async def get_project(workspace_path: str) -> dict:
        await ensure_schema(workspace_path)
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall("SELECT * FROM projects WHERE workspace_path = ?", (workspace_path,))
            if not cursor:
                return {"status": "not_found"}
            return {"status": "ok", "project": dict(cursor[0])}

    @mcp.tool
    async def detect_project(path: str) -> dict:
        seja_dir = os.path.join(path, ".seja")
        if os.path.isdir(seja_dir):
            return {"status": "detected", "workspace_path": path}
        return {"status": "not_found"}

    @mcp.tool
    async def get_project_status(workspace_path: str) -> dict:
        await ensure_schema(workspace_path)
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall("SELECT * FROM projects WHERE workspace_path = ?", (workspace_path,))
            if not cursor:
                return {"status": "not_found"}
            p = dict(cursor[0])

            pending = await db.execute_fetchall(
                "SELECT COUNT(*) as cnt FROM pending_actions WHERE project_id = ? AND status = 'open'",
                (p["id"],),
            )

            phases = await db.execute_fetchall(
                "SELECT to_phase, COUNT(*) as cnt "
                "FROM lifecycle_history WHERE project_id = ? "
                "GROUP BY to_phase ORDER BY MAX(created_at) DESC",
                (p["id"],),
            )

            return {
                "status": "ok",
                "project": p,
                "pending_count": pending[0]["cnt"],
                "phase_history": [dict(r) for r in phases],
            }
