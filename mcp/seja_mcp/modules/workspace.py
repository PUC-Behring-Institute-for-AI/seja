import os
import subprocess

from seja_mcp.sync.indexer import is_database_empty, reindex_from_markdown


def register_tools(mcp):

    @mcp.tool
    async def sync(workspace_path: str) -> dict:
        if not os.path.isdir(os.path.join(workspace_path, ".seja")):
            return {"status": "error", "error": "No .seja directory found"}

        if await is_database_empty(workspace_path):
            result = await reindex_from_markdown(workspace_path)
            return result

        return {"status": "skipped", "reason": "Database has data — export only"}

    @mcp.tool
    async def list_worktrees(workspace_path: str) -> dict:
        try:
            result = subprocess.run(
                ["git", "worktree", "list"],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                check=True,
            )
            lines = result.stdout.strip().split("\n")
            worktrees = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    worktrees.append({"path": parts[0], "branch": parts[1].strip("[]")})
            return {"status": "ok", "worktrees": worktrees}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error": e.stderr}

    @mcp.tool
    async def validate_worktree(workspace_path: str) -> dict:
        cwd = os.getcwd()
        expected = os.environ.get("SEJA_WORKTREE_PATH", workspace_path)
        return {
            "status": "ok",
            "cwd": cwd,
            "expected_worktree": expected,
            "valid": cwd == expected,
        }
