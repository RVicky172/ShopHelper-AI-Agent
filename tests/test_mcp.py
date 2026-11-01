from fakes import ScriptedChatModel, call, say
from langgraph.checkpoint.memory import InMemorySaver

from shophelper.mcp_client import mcp_tools
from shophelper.memory import InMemoryHistory
from shophelper.service import ShopHelperService


async def test_mcp_server_exposes_tools_and_agent_uses_them():
    async with mcp_tools() as tools:
        assert {t.name for t in tools} == {"get_order_status", "search_policy"}

        status = await tools[0].ainvoke({"order_id": "1002"}) if tools[0].name == "get_order_status" \
            else await tools[1].ainvoke({"order_id": "1002"})
        assert "shipped" in str(status)

        svc = ShopHelperService(
            tools=tools,
            llm=ScriptedChatModel(script=[call("search_policy", {"query": "warranty length"}),
                                          say("1-year warranty.")]),
            checkpointer=InMemorySaver(),
            history=InMemoryHistory(),
        )
        r = await svc.chat("mcp-session", "How long is the warranty?")
        assert r.tools_used == ["search_policy"] and "warranty.md" in r.citations
