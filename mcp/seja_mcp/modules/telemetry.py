from uuid_extensions import uuid7
from datetime import datetime, timedelta

from seja_mcp.db.connection import get_db
from seja_mcp.db.schema import ensure_schema
from seja_mcp.modules import dual_write

def register_tools(mcp):

    @mcp.tool
    @dual_write()
    async def record_invocation(
        workspace_path: str,
        phase: str,
        agent: str,
        skill: str,
        action: str,
        duration_ms: int = 0,
        status: str = "success",
        error: str = "",
    ) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                await db.execute("INSERT INTO projects (id, workspace_path, name) VALUES (?, ?, ?)", (str(uuid7()), workspace_path, workspace_path.split("/")[-1]))
                await db.commit()
                cursor = await db.execute_fetchall("SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,))
            pid = cursor[0]["id"]

            tid = str(uuid7())
            await db.execute(
                "INSERT INTO telemetry (id, project_id, phase, agent, skill, action, duration_ms, status, error) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (tid, pid, phase, agent, skill, action, duration_ms, status, error or None),
            )

            cursor2 = await db.execute_fetchall(
                "SELECT retention_days FROM telemetry_config WHERE project_id = ?", (pid,)
            )
            if not cursor2:
                await db.execute(
                    "INSERT INTO telemetry_config (project_id, retention_days) VALUES (?, 90)",
                    (pid,),
                )

            await db.commit()

        return {"status": "recorded", "telemetry_id": tid}


    @mcp.tool
    async def query_telemetry(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.id FROM projects p WHERE p.workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "not_found"}
            pid = cursor[0]["id"]

            aggregation = await db.execute_fetchall(
                "SELECT skill, COUNT(*) as cnt, AVG(duration_ms) as avg_duration, "
                "SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as errors "
                "FROM telemetry WHERE project_id = ? GROUP BY skill ORDER BY cnt DESC",
                (pid,),
            )

            recent = await db.execute_fetchall(
                "SELECT phase, agent, skill, action, duration_ms, status, created_at "
                "FROM telemetry WHERE project_id = ? ORDER BY created_at DESC LIMIT 20",
                (pid,),
            )

            return {
                "status": "ok",
                "aggregation": [dict(r) for r in aggregation],
                "recent": [dict(r) for r in recent],
            }


    @mcp.tool
    async def get_anomalies(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.id FROM projects p WHERE p.workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "not_found"}
            pid = cursor[0]["id"]

            stuck_loops = await db.execute_fetchall(
                "SELECT skill, phase, COUNT(*) as cnt, "
                "COUNT(DISTINCT action) as distinct_actions, "
                "SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as failures "
                "FROM telemetry WHERE project_id = ? "
                "GROUP BY skill, phase HAVING cnt > 10 AND failures > cnt * 0.5",
                (pid,),
            )

            return {
                "status": "ok",
                "stuck_loops": [dict(r) for r in stuck_loops],
            }


    @mcp.tool
    @dual_write()
    async def rotate_telemetry(workspace_path: str, retention_days: int = 0) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.id FROM projects p WHERE p.workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "not_found"}
            pid = cursor[0]["id"]

            if retention_days > 0:
                await db.execute(
                    "INSERT OR REPLACE INTO telemetry_config (project_id, retention_days) VALUES (?, ?)",
                    (pid, retention_days),
                )
            else:
                cursor2 = await db.execute_fetchall(
                    "SELECT retention_days FROM telemetry_config WHERE project_id = ?", (pid,)
                )
                retention_days = cursor2[0]["retention_days"] if cursor2 else 90

            cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
            await db.execute(
                "DELETE FROM telemetry WHERE project_id = ? AND created_at < ?",
                (pid, cutoff),
            )
            await db.commit()

        return {"status": "rotated", "retention_days": retention_days}

