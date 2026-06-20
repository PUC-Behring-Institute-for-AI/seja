from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.modules import dual_write


def register_tools(mcp):

    @mcp.tool
    @dual_write()
    async def record_test_run(
        workspace_path: str,
        plan_id: str,
        scope: str,
        total: int,
        passed: int,
        failed: int,
        details: str = "",
    ) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall("SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,))
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            run_id = str(uuid7())
            result = "passed" if failed == 0 else "failed"
            await db.execute(
                "INSERT INTO test_runs (id, project_id, plan_id, scope, result, total, passed, failed, details) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (run_id, pid, plan_id, scope, result, total, passed, failed, details),
            )
            await db.commit()

        return {"status": "recorded", "run_id": run_id, "result": result}

    @mcp.tool
    async def get_test_results(workspace_path: str, plan_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT tr.* FROM test_runs tr "
                "JOIN projects p ON tr.project_id = p.id "
                "WHERE p.workspace_path = ? AND tr.plan_id = ? "
                "ORDER BY tr.created_at DESC",
                (workspace_path, plan_id),
            )
            return {"status": "ok", "runs": [dict(r) for r in cursor]}

    @mcp.tool
    async def get_test_summary(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.id FROM projects p WHERE p.workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "not_found"}
            pid = cursor[0]["id"]

            summary = await db.execute_fetchall(
                "SELECT plan_id, COUNT(*) as runs, "
                "SUM(CASE WHEN result = 'passed' THEN 1 ELSE 0 END) as passed_runs, "
                "SUM(failed) as total_failures "
                "FROM test_runs WHERE project_id = ? GROUP BY plan_id",
                (pid,),
            )

            return {"status": "ok", "summary": [dict(r) for r in summary]}
