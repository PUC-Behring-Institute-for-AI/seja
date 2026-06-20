from datetime import datetime

from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.modules import dual_write


def register_tools(mcp):

    @mcp.tool
    @dual_write()
    async def create_plan(workspace_path: str, title: str, goal: str, steps: list) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall("SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,))
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            plan_id = str(uuid7())
            await db.execute(
                "INSERT INTO plans (id, project_id, title, goal) VALUES (?, ?, ?, ?)",
                (plan_id, pid, title, goal),
            )

            for i, step in enumerate(steps):
                step_id = str(uuid7())
                checker = step.get("checker", "")
                await db.execute(
                    "INSERT INTO plan_steps (id, plan_id, step_number, description, checker) VALUES (?, ?, ?, ?, ?)",
                    (step_id, plan_id, i + 1, step["description"], checker or None),
                )

            await db.commit()

        return {"status": "created", "plan_id": plan_id, "step_count": len(steps)}

    @mcp.tool
    async def get_plan(workspace_path: str, plan_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.* FROM plans p "
                "JOIN projects pr ON p.project_id = pr.id "
                "WHERE pr.workspace_path = ? AND p.id = ?",
                (workspace_path, plan_id),
            )
            if not cursor:
                return {"status": "not_found"}
            plan = dict(cursor[0])

            steps = await db.execute_fetchall(
                "SELECT * FROM plan_steps WHERE plan_id = ? ORDER BY step_number",
                (plan_id,),
            )
            plan["steps"] = [dict(s) for s in steps]
            return {"status": "ok", "plan": plan}

    @mcp.tool
    async def list_plans(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.id, p.title, p.goal, p.status, p.created_at FROM plans p "
                "JOIN projects pr ON p.project_id = pr.id "
                "WHERE pr.workspace_path = ? ORDER BY p.created_at DESC",
                (workspace_path,),
            )
            return {"status": "ok", "plans": [dict(r) for r in cursor]}

    @mcp.tool
    @dual_write()
    async def approve_plan(workspace_path: str, plan_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.* FROM plans p "
                "JOIN projects pr ON p.project_id = pr.id "
                "WHERE pr.workspace_path = ? AND p.id = ?",
                (workspace_path, plan_id),
            )
            if not cursor:
                return {"status": "not_found"}
            if cursor[0]["status"] != "draft":
                return {"status": "error", "error": f"Plan status is {cursor[0]['status']}, expected 'draft'"}

            now = datetime.now().isoformat()
            await db.execute(
                "UPDATE plans SET status = 'approved', approved_at = ? WHERE id = ?",
                (now, plan_id),
            )
            await db.commit()

        return {"status": "approved", "plan_id": plan_id}

    @mcp.tool
    @dual_write()
    async def update_step_status(workspace_path: str, plan_id: str, step_number: int, new_status: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT * FROM plan_steps WHERE plan_id = ? AND step_number = ?",
                (plan_id, step_number),
            )
            if not cursor:
                return {"status": "not_found"}
            if step_number > 1:
                prev = await db.execute_fetchall(
                    "SELECT * FROM plan_steps WHERE plan_id = ? AND step_number = ?",
                    (plan_id, step_number - 1),
                )
                if prev and prev[0]["checker"] and not prev[0]["checker_done_at"]:
                    return {
                        "status": "error",
                        "error": f"D16: Step {step_number - 1} checker not done. Cannot proceed to step {step_number}.",
                    }

            now = datetime.now().isoformat()
            if new_status == "done":
                await db.execute(
                    "UPDATE plan_steps SET status = ?, checker_done_at = ? WHERE plan_id = ? AND step_number = ?",
                    (new_status, now, plan_id, step_number),
                )
            else:
                await db.execute(
                    "UPDATE plan_steps SET status = ? WHERE plan_id = ? AND step_number = ?",
                    (new_status, plan_id, step_number),
                )
            await db.commit()

        return {"status": "updated", "plan_id": plan_id, "step_number": step_number, "new_status": new_status}

    @mcp.tool
    @dual_write()
    async def mark_step_checker_done(workspace_path: str, plan_id: str, step_number: int) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT * FROM plan_steps WHERE plan_id = ? AND step_number = ?",
                (plan_id, step_number),
            )
            if not cursor:
                return {"status": "not_found"}
            if not cursor[0]["checker"]:
                return {"status": "error", "error": "Step has no checker defined"}

            now = datetime.now().isoformat()
            await db.execute(
                "UPDATE plan_steps SET checker_done_at = ? WHERE plan_id = ? AND step_number = ?",
                (now, plan_id, step_number),
            )
            await db.commit()

        return {"status": "checker_done", "plan_id": plan_id, "step_number": step_number}

    @mcp.tool
    async def get_last_approved_plan(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.* FROM plans p "
                "JOIN projects pr ON p.project_id = pr.id "
                "WHERE pr.workspace_path = ? AND p.status = 'approved' "
                "ORDER BY p.approved_at DESC LIMIT 1",
                (workspace_path,),
            )
            if not cursor:
                return {"status": "not_found"}
            plan = dict(cursor[0])

            steps = await db.execute_fetchall(
                "SELECT * FROM plan_steps WHERE plan_id = ? ORDER BY step_number",
                (plan["id"],),
            )
            plan["steps"] = [dict(s) for s in steps]
            return {"status": "ok", "plan": plan}
