from functools import wraps

from seja_mcp.sync.markdown_export import export_markdown_for


def dual_write(workspace_arg_pos: int = 0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            workspace_path = kwargs.get("workspace_path")
            if workspace_path is None and len(args) > workspace_arg_pos:
                workspace_path = args[workspace_arg_pos]

            result = await func(*args, **kwargs)

            if workspace_path and not result.get("_skip_export"):
                export_result = await export_markdown_for(workspace_path)
                if export_result.get("status") == "error":
                    result["_export_warning"] = export_result.get("error")

            return result

        return wrapper

    return decorator
