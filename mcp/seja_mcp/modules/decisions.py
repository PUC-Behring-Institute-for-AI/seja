from datetime import datetime

from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.modules import dual_write


def register_tools(mcp):

    def _generate_decision_id(project_id: str) -> str:
        import hashlib

        hash_int = int(hashlib.sha256(project_id.encode()).hexdigest()[:8], 16) % 999
        return f"D-{hash_int:03d}"

    @mcp.tool
    async def get_decision(workspace_path: str, decision_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT d.* FROM decisions d "
                "JOIN projects p ON d.project_id = p.id "
                "WHERE p.workspace_path = ? AND d.id = ?",
                (workspace_path, decision_id),
            )
            if not cursor:
                return {"status": "not_found"}
            return {"status": "ok", "decision": dict(cursor[0])}

    @mcp.tool
    async def list_decisions(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT d.id, d.title, d.status, d.created_at FROM decisions d "
                "JOIN projects p ON d.project_id = p.id "
                "WHERE p.workspace_path = ? ORDER BY d.created_at DESC",
                (workspace_path,),
            )
            return {"status": "ok", "decisions": [dict(r) for r in cursor]}

    @mcp.tool
    async def search_decisions(workspace_path: str, query: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT d.id, d.title, d.status, d.created_at FROM decisions d "
                "JOIN projects p ON d.project_id = p.id "
                "JOIN decisions_fts fts ON d.id = fts.id "
                "WHERE p.workspace_path = ? AND decisions_fts MATCH ?",
                (workspace_path, query),
            )
            return {"status": "ok", "results": [dict(r) for r in cursor]}

    @mcp.tool
    @dual_write()
    async def create_decision(
        workspace_path: str,
        title: str,
        context: str,
        decision: str,
        rationale: str,
        supersedes: str = "",
    ) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall("SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,))
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            decision_id = _generate_decision_id(pid) + "-" + str(uuid7())[:8]
            now = datetime.now().isoformat()

            await db.execute(
                "INSERT INTO decisions (id, project_id, title, context, decision, rationale, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'accepted', ?)",
                (decision_id, pid, title, context, decision, rationale, now),
            )

            if supersedes:
                await db.execute(
                    "UPDATE decisions SET status = 'superseded', "
                    "superseded_by = ? WHERE id = ? AND status = 'accepted'",
                    (decision_id, supersedes),
                )
                await db.execute(
                    "UPDATE decisions SET supersedes = ? WHERE id = ?",
                    (supersedes, decision_id),
                )

            await db.commit()

        return {"status": "created", "decision_id": decision_id}

    @mcp.tool
    async def export(workspace_path: str) -> dict:
        from seja_mcp.sync.markdown_export import export_markdown_for

        result = await export_markdown_for(workspace_path)
        return result

    @mcp.tool
    async def get_decision_digest(workspace_path: str, decision_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT d.* FROM decisions d "
                "JOIN projects p ON d.project_id = p.id "
                "WHERE p.workspace_path = ? AND d.id = ?",
                (workspace_path, decision_id),
            )
            if not cursor:
                return {"status": "not_found"}
            d = dict(cursor[0])
            digest = (
                f"## {d['title']}\n\n"
                f"**Problem:** {d['context'][:200]}...\n\n"
                f"**Chosen:** {d['decision'][:200]}...\n\n"
                f"**Why:** {d['rationale'][:200]}...\n\n"
                f"**Status:** {d['status']}"
            )
            return {"status": "ok", "digest": digest, "full": d}
