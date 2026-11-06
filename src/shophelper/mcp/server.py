"""Step 7: ShopHelper's read-only tools as an MCP server (FastMCP).

Any MCP client can use them - the ShopHelper agent, Claude Desktop/Code, MCP Inspector:
    python -m shophelper.mcp.server            # stdio (default, what the agent uses)
    python -m shophelper.mcp.server --http     # streamable HTTP on :8765/mcp
Note: with stdio, stdout is the protocol channel - never print() in this process.
"""

import sys
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from shophelper.accounts import auth
from shophelper.agent import tools
from shophelper.core import identity
from shophelper.core.config import get_settings

mcp = FastMCP("shophelper", host=get_settings().mcp_host, port=8765)


def _caller(ctx: Context) -> int | None:
    """The signed user id from the Authorization header. Unlike a tool argument, the model can't
    see or set a header, and FastMCP keeps `ctx` out of the schema the model is shown."""
    request = ctx.request_context.request
    header = request.headers.get("authorization", "") if request else ""
    return auth.verify_internal_token(header.removeprefix("Bearer "))


@mcp.tool()
def get_order_status(order_id: str, ctx: Context) -> dict[str, Any]:
    """Look up an order by its numeric order ID (e.g. '1001'): status, item, total and dates."""
    if not get_settings().accounts_enabled:
        return tools.get_order_status(order_id)
    user_id = _caller(ctx)
    if user_id is None:  # the same reply as for a missing order
        return {"error": f"No order found with id {order_id}"}
    with identity.acting_as(user_id):
        return tools.get_order_status(order_id)


@mcp.tool()
def search_policy(query: str) -> dict[str, Any]:
    """Search store policies: returns, refunds, shipping, warranty, cancellation, payments,
    privacy and price adjustments. Returns the most relevant passages with their source."""
    return tools.search_policy(query)


if __name__ == "__main__":
    mcp.run(transport="streamable-http" if "--http" in sys.argv else "stdio")
