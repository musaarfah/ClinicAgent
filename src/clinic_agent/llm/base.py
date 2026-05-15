from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCallRequest:
    name: str
    arguments: dict
    call_id: str | None = None


@dataclass(frozen=True)
class ToolMessage:
    call_id: str
    name: str
    content: str


@dataclass(frozen=True)
class ToolPlan:
    assistant_message: dict | None = None
    calls: list[ToolCallRequest] = field(default_factory=list)


class LlmProvider(ABC):
    supports_tool_calling = False

    @abstractmethod
    async def generate(self, messages: list[dict[str, str]], tool_results: list[dict]) -> str:
        raise NotImplementedError

    async def plan_tools(self, messages: list[dict], tools: list[dict]) -> ToolPlan:
        return ToolPlan()

    async def generate_after_tools(
        self,
        messages: list[dict],
        assistant_message: dict | None,
        tool_messages: list[ToolMessage],
    ) -> str:
        tool_results = [{"name": item.name, "result": item.content} for item in tool_messages]
        return await self.generate(messages=messages, tool_results=tool_results)
