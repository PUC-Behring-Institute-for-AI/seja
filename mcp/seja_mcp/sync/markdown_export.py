import os
import hashlib
import json
from datetime import datetime

from seja_mcp.db.connection import get_db


def _compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _atomic_write(file_path: str, content: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    tmp_path = file_path + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(content)
    os.replace(tmp_path, file_path)


async def _log_export(workspace_path: str, module: str, file_path: str, sha256: str, status: str = "success", error: str = ""):
    from uuid_extensions import uuid7
    async with get_db(workspace_path) as db:
        await db.execute(
            "INSERT INTO export_log (id, workspace_path, module, file_path, sha256, status, error) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid7()), workspace_path, module, file_path, sha256, status, error or None),
        )
        await db.commit()


async def export_markdown_for(workspace_path: str, module: str = ""):
    base_dir = os.path.join(workspace_path, ".seja")
    errors = []

    async with get_db(workspace_path) as db:
        project_row = await db.execute_fetchall(
            "SELECT * FROM projects WHERE workspace_path = ?", (workspace_path,)
        )
        if not project_row:
            return {"status": "error", "error": "No project found"}
        project = dict(project_row[0])

        await db.execute(
            "UPDATE projects SET last_export_attempt = ? WHERE id = ?",
            (datetime.now().isoformat(), project["id"]),
        )
        await db.commit()

        try:
            _atomic_write(
                os.path.join(base_dir, "project.md"),
                f"# {project['name']}\n\n"
                f"- **Phase**: {project['phase']}\n"
                f"- **Path**: {project['workspace_path']}\n"
                f"- **Version**: {project['version']}\n"
                f"- **Created**: {project['created_at']}\n"
                f"- **Updated**: {project['updated_at']}\n",
            )

            rows = await db.execute_fetchall(
                "SELECT * FROM constitution_principles WHERE project_id = ? ORDER BY rank",
                (project["id"],),
            )
            if rows:
                principles = "\n\n".join(
                    f"## {r['rank']}. {r['principle']}\n\n{r['description']}"
                    for r in rows
                )
                _atomic_write(
                    os.path.join(base_dir, "constitution.md"),
                    f"# Constitution\n\n{principles}\n",
                )

            decisions_dir = os.path.join(base_dir, "decisions")
            rows = await db.execute_fetchall(
                "SELECT * FROM decisions WHERE project_id = ? ORDER BY created_at",
                (project["id"],),
            )
            for d in rows:
                content = (
                    f"# {d['title']}\n\n"
                    f"**Status**: {d['status']}\n"
                    f"**Created**: {d['created_at']}\n\n"
                    f"## Context\n\n{d['context']}\n\n"
                    f"## Decision\n\n{d['decision']}\n\n"
                    f"## Rationale\n\n{d['rationale']}\n"
                )
                path = os.path.join(decisions_dir, f"{d['id']}.md")
                _atomic_write(path, content)

            plans_dir = os.path.join(base_dir, "plans")
            rows = await db.execute_fetchall(
                "SELECT * FROM plans WHERE project_id = ? ORDER BY created_at",
                (project["id"],),
            )
            for p in rows:
                content = (
                    f"# {p['title']}\n\n"
                    f"**Goal**: {p['goal']}\n"
                    f"**Status**: {p['status']}\n"
                    f"**Created**: {p['created_at']}\n\n"
                    f"## Steps\n\n"
                )
                steps = await db.execute_fetchall(
                    "SELECT * FROM plan_steps WHERE plan_id = ? ORDER BY step_number",
                    (p["id"],),
                )
                for s in steps:
                    content += (
                        f"- **{s['step_number']}.** {s['description']}"
                        f" [{s['status']}]"
                        f"{' (checker: ' + s['checker'] + ')' if s['checker'] else ''}\n"
                    )
                _atomic_write(os.path.join(plans_dir, f"plan-{p['id']}.md"), content)

            rows = await db.execute_fetchall(
                "SELECT * FROM research_reports WHERE project_id = ? ORDER BY created_at",
                (project["id"],),
            )
            if rows:
                reports = "\n\n---\n\n".join(
                    f"## {r['question']}\n\n{r['findings']}\n\n"
                    f"**Sources**: {r['sources']}\n"
                    f"{'**Recommendation**: ' + r['recommendation'] if r['recommendation'] else ''}"
                    for r in rows
                )
                _atomic_write(
                    os.path.join(base_dir, "research.md"),
                    f"# Research Reports\n\n{reports}\n",
                )

            rows = await db.execute_fetchall(
                "SELECT * FROM briefs WHERE project_id = ? ORDER BY created_at",
                (project["id"],),
            )
            if rows:
                briefs_content = "# Briefs\n\n"
                for b in rows:
                    briefs_content += (
                        f"## Phase: {b['phase']} ({b['session_id']})\n\n"
                        f"**Session**: {b['session_id']} | **Status**: {b['status']}\n\n"
                        f"{b['content']}\n\n---\n\n"
                    )
                _atomic_write(os.path.join(base_dir, "briefs.md"), briefs_content)

        except Exception as e:
            errors.append(str(e))

    final_status = "error" if errors else "success"
    error_msg = "; ".join(errors) if errors else ""
    async with get_db(workspace_path) as db:
        await db.execute(
            "UPDATE projects SET last_export_success = ? WHERE id = ?",
            (datetime.now().isoformat() if final_status == "success" else None, project["id"]),
        )
        await db.commit()

    return {"status": final_status, "error": error_msg or None}


async def export_all(workspace_path: str):
    return await export_markdown_for(workspace_path)
