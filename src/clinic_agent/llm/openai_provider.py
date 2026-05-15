import json
import os

from clinic_agent.llm.base import LlmProvider, ToolCallRequest, ToolMessage, ToolPlan


class OpenAiProvider(LlmProvider):
    supports_tool_calling = True

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def generate(self, messages: list[dict[str, str]], tool_results: list[dict]) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=self._with_tool_results(messages, tool_results),
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    async def plan_tools(self, messages: list[dict], tools: list[dict]) -> ToolPlan:
        if not tools:
            return ToolPlan()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        return ToolPlan(
            assistant_message={
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tool_call.model_dump() for tool_call in tool_calls],
            },
            calls=[
                ToolCallRequest(
                    call_id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=self._parse_tool_arguments(tool_call.function.arguments),
                )
                for tool_call in tool_calls
            ],
        )

    async def generate_after_tools(
        self,
        messages: list[dict],
        assistant_message: dict | None,
        tool_messages: list[ToolMessage],
    ) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        from openai import AsyncOpenAI

        final_messages = list(messages)
        if assistant_message:
            final_messages.append(assistant_message)
        final_messages.extend(
            {
                "role": "tool",
                "tool_call_id": item.call_id,
                "name": item.name,
                "content": item.content,
            }
            for item in tool_messages
        )

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=final_messages,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    @staticmethod
    def _with_tool_results(messages: list[dict[str, str]], tool_results: list[dict]) -> list[dict[str, str]]:
        if not tool_results:
            return messages
        return [
            *messages,
            {
                "role": "system",
                "content": f"Local scheduling tool results: {tool_results}",
            },
        ]

    @staticmethod
    def _parse_tool_arguments(arguments: str) -> dict:
        try:
            parsed = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
