from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.db.schema import ensure_schema
from seja_mcp.modules import dual_write

def register_tools(mcp):

    @mcp.tool
    async def get_constitution(workspace_path: str) -> dict:
        await ensure_schema(workspace_path)
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.id FROM projects p WHERE p.workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            principles = await db.execute_fetchall(
                "SELECT * FROM constitution_principles WHERE project_id = ? ORDER BY rank",
                (pid,),
            )
            return {
                "status": "ok",
                "principles": [dict(r) for r in principles],
            }


    @mcp.tool
    async def get_principle(workspace_path: str, principle_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT cp.* FROM constitution_principles cp "
                "JOIN projects p ON cp.project_id = p.id "
                "WHERE p.workspace_path = ? AND cp.id = ?",
                (workspace_path, principle_id),
            )
            if not cursor:
                return {"status": "not_found"}
            return {"status": "ok", "principle": dict(cursor[0])}


    @mcp.tool
    async def list_principles(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT cp.id, cp.rank, cp.principle FROM constitution_principles cp "
                "JOIN projects p ON cp.project_id = p.id "
                "WHERE p.workspace_path = ? ORDER BY cp.rank",
                (workspace_path,),
            )
            return {"status": "ok", "principles": [dict(r) for r in cursor]}


    @mcp.tool
    @dual_write()
    async def check_compliance(workspace_path: str, description: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.id FROM projects p WHERE p.workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            principles = await db.execute_fetchall(
                "SELECT * FROM constitution_principles WHERE project_id = ? ORDER BY rank",
                (pid,),
            )
            description_lower = description.lower()
            violations = []
            for row in principles:
                principle_text = row["principle"].lower()
                principle_keywords = set(principle_text.split())
                if len(principle_keywords) > 2:
                    matches = sum(1 for kw in principle_keywords if kw in description_lower)
                    if matches < 1:
                        violations.append({
                            "principle_id": row["id"],
                            "principle": row["principle"],
                            "reason": f"Description does not reference principle: {row['principle']}",
                        })

            return {
                "status": "ok",
                "compliant": len(violations) == 0,
                "violations": violations,
            }

