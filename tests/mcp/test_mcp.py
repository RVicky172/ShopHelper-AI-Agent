from langgraph.checkpoint.memory import InMemorySaver

from fakes import ScriptedChatModel, say
from shophelper.agent.memory import InMemoryHistory
from shophelper.agent.service import ShopHelperService
from shophelper.mcp.client import mcp_tools


async def test_mcp_server_exposes_tools_and_agent_uses_them():
    async with mcp_tools() as tools:
        by_name = {t.name: t for t in tools}
        assert set(by_name) == {"get_order_status", "search_policy"}
        assert "shipped" in str(await by_name["get_order_status"].ainvoke({"order_id": "1002"}))

        svc = ShopHelperService(
            tools=tools,
            llm=ScriptedChatModel(script=[say("1-year warranty.")]),  # code runs the search (030)
            checkpointer=InMemorySaver(),
            history=InMemoryHistory(),
        )
        r = await svc.chat("mcp-session", "How long is the warranty?")
        assert r.tools_used == ["search_policy"] and "warranty.md" in r.citations
