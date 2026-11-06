"""MCP client side: load the MCP server's tools as LangChain tools for the graph.

Two transports, same tools:
  * MCP_URL set (local docker-compose): streamable HTTP to the `mcp` container. Each tool
    call opens a short session, so the server can restart without breaking the API.
  * MCP_URL unset (ECS): one stdio subprocess + session kept open for the life of the
    process (FastAPI lifespan), instead of spawning a server per tool call.
"""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from shophelper.accounts import auth
from shophelper.core import identity
from shophelper.core.config import get_settings


async def add_identity(request, handler):
    """Signs a fresh token for each call. With no user, no header is sent, and the server refuses."""
    user_id = identity.current_user()
    if user_id is None:
        return await handler(request)
    headers = {**(request.headers or {}), "Authorization": f"Bearer {auth.issue_internal_token(user_id)}"}
    return await handler(request.override(headers=headers))


@asynccontextmanager
async def mcp_tools() -> AsyncIterator[list[BaseTool]]:
    url = get_settings().mcp_url
    if url:
        client = MultiServerMCPClient(
            {"shophelper": {"transport": "streamable_http", "url": url}}, tool_interceptors=[add_identity]
        )
        yield await client.get_tools()
        return

    client = MultiServerMCPClient({
        "shophelper": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-m", "shophelper.mcp.server"],
            # The MCP SDK passes only a minimal env by default; the server needs
            # AWS credentials/region and our settings, so forward everything.
            "env": dict(os.environ),
        }
    })
    async with client.session("shophelper") as session:
        yield await load_mcp_tools(session)
