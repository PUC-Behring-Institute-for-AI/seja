import asyncio
import os
import logging
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from seja_mcp.db.connection import close_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seja.mcp")


def create_app() -> FastMCP:
    mcp = FastMCP("SEJA MCP Server", lifespan=lifespan)

    from seja_mcp.modules import project, constitution, decisions, design
    from seja_mcp.modules import lifecycle, pending, briefs, telemetry
    from seja_mcp.modules import plans, research, perspectives, journeys
    from seja_mcp.modules import tests, experiments, workspace

    project.register_tools(mcp)
    constitution.register_tools(mcp)
    decisions.register_tools(mcp)
    design.register_tools(mcp)
    lifecycle.register_tools(mcp)
    pending.register_tools(mcp)
    briefs.register_tools(mcp)
    telemetry.register_tools(mcp)
    plans.register_tools(mcp)
    research.register_tools(mcp)
    perspectives.register_tools(mcp)
    journeys.register_tools(mcp)
    tests.register_tools(mcp)
    experiments.register_tools(mcp)
    workspace.register_tools(mcp)

    return mcp


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    logger.info("SEJA MCP Server starting...")
    yield
    logger.info("SEJA MCP Server shutting down...")
    await close_all()


async def health_check():
    return {"status": "ok", "service": "seja-mcp", "version": "2.0.0"}


mcp_app = create_app()


async def run():
    from fastmcp import FastMCP
    port = int(os.environ.get("SEJA_MCP_PORT", "8765"))
    host = os.environ.get("SEJA_MCP_HOST", "0.0.0.0")

    async with mcp_app:
        await mcp_app.run_async(
            transport="streamable-http",
            host=host,
            port=port,
        )


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()

