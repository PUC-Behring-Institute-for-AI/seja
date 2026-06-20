from seja_mcp.db.connection import get_db
from seja_mcp.modules import dual_write


def register_tools(mcp):

    @mcp.tool
    async def get_global_metacomm(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT * FROM design_features df "
                "JOIN projects p ON df.project_id = p.id "
                "WHERE p.workspace_path = ? AND df.metacomm_type = 'global'",
                (workspace_path,),
            )
            return {"status": "ok", "features": [dict(r) for r in cursor]}

    @mcp.tool
    async def get_feature(workspace_path: str, feature_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT df.* FROM design_features df "
                "JOIN projects p ON df.project_id = p.id "
                "WHERE p.workspace_path = ? AND df.feature_id = ?",
                (workspace_path, feature_id),
            )
            if not cursor:
                return {"status": "not_found"}
            return {"status": "ok", "feature": dict(cursor[0])}

    @mcp.tool
    async def list_features(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT df.feature_id, df.as_intended, df.as_coded, df.status, df.metacomm_type "
                "FROM design_features df JOIN projects p ON df.project_id = p.id "
                "WHERE p.workspace_path = ? ORDER BY df.created_at",
                (workspace_path,),
            )
            return {"status": "ok", "features": [dict(r) for r in cursor]}

    @mcp.tool
    async def get_conventions(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT cp.principle, cp.description FROM constitution_principles cp "
                "JOIN projects p ON cp.project_id = p.id "
                "WHERE p.workspace_path = ? ORDER BY cp.rank",
                (workspace_path,),
            )
            return {"status": "ok", "conventions": [dict(r) for r in cursor]}

    @mcp.tool
    @dual_write()
    async def update_feature_as_coded(workspace_path: str, feature_id: str, as_coded: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT p.id FROM projects p WHERE p.workspace_path = ?", (workspace_path,)
            )
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            await db.execute(
                "UPDATE design_features SET as_coded = ?, status = 'coded', "
                "updated_at = datetime('now') WHERE project_id = ? AND feature_id = ?",
                (as_coded, pid, feature_id),
            )
            await db.commit()
        return {"status": "updated", "feature_id": feature_id}

    @mcp.tool
    async def diff_as_intended_vs_coded(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT df.* FROM design_features df "
                "JOIN projects p ON df.project_id = p.id "
                "WHERE p.workspace_path = ? AND df.status = 'coded' AND df.as_coded IS NOT NULL",
                (workspace_path,),
            )
            diffs = []
            for row in cursor:
                intended = row["as_intended"][:100]
                coded = row["as_coded"][:100] if row["as_coded"] else ""
                diffs.append(
                    {
                        "feature_id": row["feature_id"],
                        "as_intended": intended,
                        "as_coded": coded,
                        "has_diff": intended != coded,
                    }
                )
            return {"status": "ok", "diffs": diffs}
