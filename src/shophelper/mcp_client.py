"""MCP client side: load the MCP server's tools as LangChain tools for the graph.

One stdio subprocess + session is kept open for the life of the process (FastAPI
lifespan), instead of spawning a server per tool call.
"""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


@asynccontextmanager
async def mcp_tools() -> AsyncIterator[list[BaseTool]]:
    client = MultiServerMCPClient({
        "shophelper": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-m", "shophelper.mcp_server"],
            # The MCP SDK passes only a minimal env by default; the server needs
            # AWS credentials/region and our settings, so forward everything.
            "env": dict(os.environ),
        }
    })
    async with client.session("shophelper") as session:
        yield await load_mcp_tools(session)
