import json
from collections.abc import Mapping
from typing import Protocol

from clinic_agent.config import get_mcp_server_url


class ToolClient(Protocol):
    async def openai_definitions(self, allowed_tool_names: list[str]) -> list[dict]:
        raise NotImplementedError

    async def call_tool(self, name: str, arguments: dict, session_id: str) -> dict:
        raise NotImplementedError


class McpToolClient:
    def __init__(self, server_url: str | None = None) -> None:
        self.server_url = server_url or get_mcp_server_url()

    async def openai_definitions(self, allowed_tool_names: list[str]) -> list[dict]:
        async with self._session() as session:
            response = await session.list_tools()

        allowed = set(allowed_tool_names)
        definitions = []
        for tool in response.tools:
            tool_name = tool.name
            if tool_name not in allowed:
                continue

            parameters = self._without_session_id(tool.inputSchema)
            definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool.description or "",
                        "parameters": parameters,
                    },
                }
            )
        return definitions

    async def call_tool(self, name: str, arguments: dict, session_id: str) -> dict:
        mcp_arguments = dict(arguments)
        if name not in {"patient_search", "get_location_details"}:
            mcp_arguments["session_id"] = session_id

        async with self._session() as session:
            result = await session.call_tool(name, arguments=mcp_arguments)
        return parse_mcp_result(result)

    def _session(self):
        return open_mcp_session(self.server_url)

    @staticmethod
    def _without_session_id(input_schema: Mapping) -> dict:
        schema = dict(input_schema or {})
        properties = dict(schema.get("properties", {}))
        properties.pop("session_id", None)
        schema["properties"] = properties
        schema["required"] = [
            field_name
            for field_name in schema.get("required", [])
            if field_name != "session_id"
        ]
        return schema


def parse_mcp_result(result) -> dict:
    structured_content = getattr(result, "structuredContent", None)
    if structured_content is not None:
        return structured_content

    content_items = getattr(result, "content", [])
    if not content_items:
        return {}

    first_item = content_items[0]
    text = getattr(first_item, "text", None)
    if text is None:
        return {"content": str(first_item)}

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"content": text}

    if isinstance(parsed, dict):
        return parsed
    return {"content": parsed}


def open_mcp_session(server_url: str):
    from contextlib import asynccontextmanager

    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    @asynccontextmanager
    async def session_context():
        async with streamablehttp_client(server_url) as streams:
            read_stream, write_stream, *_ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    return session_context()


def create_tool_client() -> ToolClient:
    return McpToolClient()
