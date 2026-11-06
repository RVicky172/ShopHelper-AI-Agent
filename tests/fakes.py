"""A scripted chat model so the LangGraph agent can be tested offline."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ScriptedChatModel(BaseChatModel):
    script: list[AIMessage]
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls += 1
        msg = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        return ChatResult(generations=[ChatGeneration(message=msg.model_copy())])


def call(name: str, args: dict, id: str = "c1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": id}],
                     usage_metadata={"input_tokens": 100, "output_tokens": 10, "total_tokens": 110})


def say(text: str) -> AIMessage:
    return AIMessage(content=text,
                     usage_metadata={"input_tokens": 120, "output_tokens": 20, "total_tokens": 140})
