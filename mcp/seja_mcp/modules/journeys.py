from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.modules import dual_write


def register_tools(mcp):

    @mcp.tool
    @dual_write()
    async def create_journey(
        workspace_path: str,
        feature_id: str,
        jm_tb: str,
        jm_e: str = "",
        journey_type: str = "designed",
    ) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall("SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,))
            if not cursor:
                return {"status": "error", "error": "Project not found"}
            pid = cursor[0]["id"]

            journey_id = str(uuid7())
            await db.execute(
                "INSERT INTO journey_maps (id, project_id, feature_id, jm_tb, jm_e, journey_type) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (journey_id, pid, feature_id, jm_tb, jm_e or None, journey_type),
            )
            await db.commit()

        return {"status": "created", "journey_id": journey_id}

    @mcp.tool
    async def get_journey(workspace_path: str, journey_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT j.* FROM journey_maps j "
                "JOIN projects p ON j.project_id = p.id "
                "WHERE p.workspace_path = ? AND j.id = ?",
                (workspace_path, journey_id),
            )
            if not cursor:
                return {"status": "not_found"}
            return {"status": "ok", "journey": dict(cursor[0])}

    @mcp.tool
    async def list_journeys(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT j.id, j.feature_id, j.journey_type, j.created_at FROM journey_maps j "
                "JOIN projects p ON j.project_id = p.id "
                "WHERE p.workspace_path = ? ORDER BY j.created_at DESC",
                (workspace_path,),
            )
            return {"status": "ok", "journeys": [dict(r) for r in cursor]}

    @mcp.tool
    async def get_semiotic_report(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT j.* FROM journey_maps j JOIN projects p ON j.project_id = p.id WHERE p.workspace_path = ?",
                (workspace_path,),
            )

            journey_types = {}
            gaps = []
            for row in cursor:
                jt = row["journey_type"]
                journey_types[jt] = journey_types.get(jt, 0) + 1
                if row["jm_e"] and row["jm_tb"] != row["jm_e"]:
                    gaps.append(
                        {
                            "feature_id": row["feature_id"],
                            "designed": row["jm_tb"][:100],
                            "implemented": row["jm_e"][:100],
                            "gap_size": abs(len(row["jm_tb"]) - len(row["jm_e"])),
                        }
                    )

            await db.execute_fetchall(
                "SELECT * FROM design_features df JOIN projects p ON df.project_id = p.id WHERE p.workspace_path = ?",
                (workspace_path,),
            )

            return {
                "status": "ok",
                "journey_counts": journey_types,
                "semiotic_gaps": gaps,
                "gap_count": len(gaps),
            }
