import asyncio
import os
import subprocess

from uuid_extensions import uuid7

from seja_mcp.db.connection import get_db
from seja_mcp.modules import dual_write


def register_tools(mcp):

    _experiment_lock = asyncio.Lock()

    def _get_worktree_path(workspace_path: str, experiment_name: str) -> str:
        return os.path.join(workspace_path, "..", f".worktree-{experiment_name}")

    def _validate_cwd(workspace_path: str, experiment_name: str = "") -> dict:
        cwd = os.getcwd()
        expected = workspace_path
        if experiment_name:
            wt = _get_worktree_path(workspace_path, experiment_name)
            cwd_valid = cwd == wt or cwd == workspace_path
        else:
            cwd_valid = cwd == workspace_path

        if not cwd_valid:
            return {"valid": False, "cwd": cwd, "expected": expected}
        return {"valid": True, "cwd": cwd}

    @mcp.tool
    @dual_write()
    async def fork_experiment(workspace_path: str, name: str, branch: str = "") -> dict:
        async with _experiment_lock:
            async with get_db(workspace_path) as db:
                cursor = await db.execute_fetchall(
                    "SELECT id FROM projects WHERE workspace_path = ?", (workspace_path,)
                )
                if not cursor:
                    return {"status": "error", "error": "Project not found"}
                pid = cursor[0]["id"]

                duplicate = await db.execute_fetchall(
                    "SELECT 1 FROM experiments WHERE project_id = ? AND name = ?",
                    (pid, name),
                )
                if duplicate:
                    return {"status": "error", "error": f"Experiment '{name}' already exists"}

            if not os.path.isdir(os.path.join(workspace_path, ".git")):
                return {"status": "error", "error": "Workspace is not a git repository"}

            exp_branch = branch or f"exp/{name}"
            worktree_path = _get_worktree_path(workspace_path, name)

            try:
                subprocess.run(
                    ["git", "worktree", "add", "-b", exp_branch, worktree_path, "HEAD"],
                    cwd=workspace_path,
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                return {"status": "error", "error": f"Git worktree failed: {e.stderr}"}

            async with get_db(workspace_path) as db:
                exp_id = str(uuid7())
                await db.execute(
                    "INSERT INTO experiments (id, project_id, name, branch, worktree_path) VALUES (?, ?, ?, ?, ?)",
                    (exp_id, pid, name, exp_branch, worktree_path),
                )
                await db.commit()

        return {
            "status": "forked",
            "experiment_id": exp_id,
            "branch": exp_branch,
            "worktree_path": worktree_path,
        }

    @mcp.tool
    async def list_experiments(workspace_path: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT e.id, e.name, e.branch, e.status, e.semiotic_score, e.created_at "
                "FROM experiments e JOIN projects p ON e.project_id = p.id "
                "WHERE p.workspace_path = ? ORDER BY e.created_at DESC",
                (workspace_path,),
            )
            return {"status": "ok", "experiments": [dict(r) for r in cursor]}

    @mcp.tool
    async def get_experiment_status(workspace_path: str, experiment_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT e.* FROM experiments e "
                "JOIN projects p ON e.project_id = p.id "
                "WHERE p.workspace_path = ? AND e.id = ?",
                (workspace_path, experiment_id),
            )
            if not cursor:
                return {"status": "not_found"}
            exp = dict(cursor[0])

            werk_exists = os.path.isdir(exp["worktree_path"])
            return {
                "status": "ok",
                "experiment": exp,
                "worktree_exists": werk_exists,
            }

    @mcp.tool
    async def compare_experiments(workspace_path: str, experiment_ids: list) -> dict:
        async with get_db(workspace_path) as db:
            results = []
            for eid in experiment_ids:
                cursor = await db.execute_fetchall(
                    "SELECT e.* FROM experiments e "
                    "JOIN projects p ON e.project_id = p.id "
                    "WHERE p.workspace_path = ? AND e.id = ?",
                    (workspace_path, eid),
                )
                if cursor:
                    exp = dict(cursor[0])
                    werk_exists = os.path.isdir(exp["worktree_path"])
                    results.append(
                        {
                            "id": eid,
                            "name": exp["name"],
                            "branch": exp["branch"],
                            "semiotic_score": exp["semiotic_score"],
                            "worktree_exists": werk_exists,
                        }
                    )

            return {
                "status": "ok",
                "experiments": results,
                "comparison": results,
            }

    @mcp.tool
    @dual_write()
    async def merge_experiment(workspace_path: str, experiment_id: str, continue_merge: bool = False) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT e.* FROM experiments e "
                "JOIN projects p ON e.project_id = p.id "
                "WHERE p.workspace_path = ? AND e.id = ?",
                (workspace_path, experiment_id),
            )
            if not cursor:
                return {"status": "not_found"}
            exp = dict(cursor[0])

            if exp["status"] == "merged":
                return {"status": "error", "error": "Experiment already merged"}

            try:
                if continue_merge:
                    subprocess.run(
                        ["git", "merge", "--continue", "--no-edit"],
                        cwd=workspace_path,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                else:
                    subprocess.run(
                        ["git", "merge", exp["branch"]],
                        cwd=workspace_path,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
            except subprocess.CalledProcessError as e:
                stderr = e.stderr or ""
                if "CONFLICT" in stderr:
                    return {
                        "status": "conflict",
                        "experiment_id": experiment_id,
                        "error": (
                            "Merge conflict detected. Resolve manually, "
                            "then call merge_experiment with continue_merge=true"
                        ),
                        "details": stderr,
                    }
                return {"status": "error", "error": f"Merge failed: {stderr}"}

            await db.execute("UPDATE experiments SET status = 'merged' WHERE id = ?", (experiment_id,))
            await db.commit()

        return {"status": "merged", "experiment_id": experiment_id}

    @mcp.tool
    @dual_write()
    async def discard_experiment(workspace_path: str, experiment_id: str) -> dict:
        async with get_db(workspace_path) as db:
            cursor = await db.execute_fetchall(
                "SELECT e.* FROM experiments e "
                "JOIN projects p ON e.project_id = p.id "
                "WHERE p.workspace_path = ? AND e.id = ?",
                (workspace_path, experiment_id),
            )
            if not cursor:
                return {"status": "not_found"}
            exp = dict(cursor[0])

            worktree_path = exp["worktree_path"]
            branch = exp["branch"]

            if os.path.isdir(worktree_path):
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", worktree_path],
                        cwd=workspace_path,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                except subprocess.CalledProcessError:
                    pass

            try:
                subprocess.run(
                    ["git", "branch", "-D", branch],
                    cwd=workspace_path,
                    capture_output=True,
                    text=True,
                )
            except Exception:
                pass

            await db.execute(
                "UPDATE experiments SET status = 'discarded' WHERE id = ?",
                (experiment_id,),
            )
            await db.commit()

        return {
            "status": "discarded",
            "experiment_id": experiment_id,
            "worktree_removed": not os.path.isdir(worktree_path),
        }
