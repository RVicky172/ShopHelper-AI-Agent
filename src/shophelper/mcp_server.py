"""Step 7: ShopHelper's read-only tools as an MCP server (FastMCP).

Any MCP client can use them - the ShopHelper agent, Claude Desktop/Code, MCP Inspector:
    python -m shophelper.mcp_server            # stdio (default, what the agent uses)
    python -m shophelper.mcp_server --http     # streamable HTTP on :8765/mcp
Note: with stdio, stdout is the protocol channel - never print() in this process.
"""

import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from shophelper import tools

mcp = FastMCP("shophelper", port=8765)


@mcp.tool()
def get_order_status(order_id: str) -> dict[str, Any]:
    """Look up an order by its numeric order ID (e.g. '1001'): status, item, total and dates."""
    return tools.get_order_status(order_id)


@mcp.tool()
def search_policy(query: str) -> dict[str, Any]:
    """Search store policies: returns, refunds, shipping, warranty, cancellation, payments,
    privacy and price adjustments. Returns the most relevant passages with their source."""
    return tools.search_policy(query)


if __name__ == "__main__":
    mcp.run(transport="streamable-http" if "--http" in sys.argv else "stdio")
