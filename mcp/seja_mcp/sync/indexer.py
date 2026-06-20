import os
import re
import yaml

from seja_mcp.db.connection import get_db


DECISION_RE = re.compile(r"^D-\d{3}")


async def is_database_empty(workspace_path: str = "") -> bool:
    async with get_db(workspace_path) as db:
        cursor = await db.execute_fetchall(
            "SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table' AND name='projects'"
        )
        if cursor[0]["cnt"] == 0:
            return True
        cursor = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM projects")
        return cursor[0]["cnt"] == 0


async def reindex_from_markdown(workspace_path: str):
    if not await is_database_empty(workspace_path):
        return {"status": "skipped", "reason": "Database is not empty — warm start, no reindex"}

    base_dir = os.path.join(workspace_path, ".seja")
    if not os.path.isdir(base_dir):
        return {"status": "skipped", "reason": "No .seja directory found"}

    from uuid_extensions import uuid7

    async with get_db(workspace_path) as db:
        project_md = os.path.join(base_dir, "project.md")
        if os.path.exists(project_md):
            with open(project_md) as f:
                content = f.read()
            name_match = re.search(r"^# (.+)", content)
            phase_match = re.search(r"\*\*Phase\*\*: (\w+)", content)
            if name_match:
                pid = str(uuid7())
                await db.execute(
                    "INSERT OR IGNORE INTO projects (id, workspace_path, name, phase) "
                    "VALUES (?, ?, ?, ?)",
                    (pid, workspace_path, name_match.group(1), phase_match.group(1) if phase_match else "setup"),
                )

        constitution_md = os.path.join(base_dir, "constitution.md")
        if os.path.exists(constitution_md):
            with open(constitution_md) as f:
                content = f.read()
            sections = re.findall(r"^## (\d+)\.\s+(.+?)\n\n(.+?)(?=\n## |\Z)", content, re.MULTILINE | re.DOTALL)
            for rank_str, principle, description in sections:
                pid = str(uuid7())
                pid_project = str(uuid7())
                await db.execute(
                    "INSERT OR IGNORE INTO constitution_principles (id, project_id, rank, principle, description) "
                    "VALUES (?, (SELECT id FROM projects WHERE workspace_path = ?), ?, ?, ?)",
                    (pid, workspace_path, int(rank_str), principle.strip(), description.strip()),
                )

        decisions_dir = os.path.join(base_dir, "decisions")
        if os.path.isdir(decisions_dir):
            for fname in sorted(os.listdir(decisions_dir)):
                if fname.endswith(".md") and DECISION_RE.match(fname):
                    with open(os.path.join(decisions_dir, fname)) as f:
                        content = f.read()
                    title = ""
                    status = "accepted"
                    for line in content.split("\n"):
                        if line.startswith("# "):
                            title = line[2:]
                        if line.startswith("**Status**"):
                            status = line.split(":")[1].strip().lower()
                    pid = str(uuid7())
                    await db.execute(
                        "INSERT OR IGNORE INTO decisions "
                        "(id, project_id, title, context, decision, rationale, status) "
                        "VALUES (?, (SELECT id FROM projects WHERE workspace_path = ?), ?, '', '', ?, ?)",
                        (pid, workspace_path, title, title, status),
                    )

        await db.commit()

    return {"status": "reindexed", "tables": ["projects", "constitution_principles", "decisions"]}
