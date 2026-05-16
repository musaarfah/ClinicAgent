import json
import re
from uuid import uuid4

from clinic_agent.agent.skills import tools_for_skills
from clinic_agent.api.schemas import ChatResponse, ToolResultResponse
from clinic_agent.llm.base import LlmProvider, ToolCallRequest, ToolMessage
from clinic_agent.memory.store import ConversationMemory
from clinic_agent.prompts.system_prompt import build_system_prompt
from clinic_agent.tools.client import ToolClient


class AgentOrchestrator:
    def __init__(
        self,
        llm_provider: LlmProvider,
        memory: ConversationMemory,
        tool_client: ToolClient,
        enabled_skills: list[str] | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.memory = memory
        self.tool_client = tool_client
        self.enabled_tools = tools_for_skills(enabled_skills or ["appointment_scheduling", "handoff"])

    async def handle_message(self, user_message: str, session_id: str | None = None) -> ChatResponse:
        active_session_id = session_id or str(uuid4())
        self.memory.add_message(active_session_id, "user", user_message)

        messages = self._build_messages(active_session_id)
        tool_results = await self._run_tools(active_session_id, user_message, messages)
        if tool_results:
            self.memory.add_message(
                active_session_id,
                "tool",
                "\n".join(f"{item.name}: {item.result}" for item in tool_results),
            )

        assistant_message = await self._generate_response(
            session_id=active_session_id,
            messages=messages,
            tool_results=tool_results,
        )
        self.memory.add_message(active_session_id, "assistant", assistant_message)

        return ChatResponse(
            session_id=active_session_id,
            message=assistant_message,
            tool_results=tool_results,
        )

    async def _run_tools(
        self,
        session_id: str,
        user_message: str,
        messages: list[dict],
    ) -> list[ToolResultResponse]:
        if self.llm_provider.supports_tool_calling:
            return await self._run_provider_requested_tools(session_id, messages)
        return await self._run_keyword_tools(session_id, user_message)

    async def _run_provider_requested_tools(
        self,
        session_id: str,
        messages: list[dict],
    ) -> list[ToolResultResponse]:
        plan = await self.llm_provider.plan_tools(
            messages=messages,
            tools=await self.tool_client.openai_definitions(self.enabled_tools),
        )
        self._last_assistant_tool_message = plan.assistant_message
        self._last_direct_provider_message = None
        if plan.assistant_message and not plan.calls:
            self._last_direct_provider_message = plan.assistant_message.get("content")
        self._last_tool_messages: list[ToolMessage] = []

        results: list[ToolResultResponse] = []
        for tool_call in plan.calls:
            if tool_call.name not in self.enabled_tools:
                continue
            result = await self._execute_tool(session_id, tool_call)
            results.append(ToolResultResponse(name=tool_call.name, result=result))
            if tool_call.call_id:
                self._last_tool_messages.append(
                    ToolMessage(
                        call_id=tool_call.call_id,
                        name=tool_call.name,
                        content=json.dumps(result),
                    )
                )
        return results

    async def _run_keyword_tools(self, session_id: str, user_message: str) -> list[ToolResultResponse]:
        normalized_message = user_message.lower()
        tool_requests: list[tuple[str, dict]] = []

        if any(word in normalized_message for word in ["find", "patient", "name"]):
            tool_requests.append(("patient_search", {"query": user_message}))

        if "dob" in normalized_message or "date of birth" in normalized_message:
            tool_requests.append(("validate_patient", self._extract_validation_arguments(user_message)))

        if any(word in normalized_message for word in ["my appointment", "appointments do i", "what appointments"]):
            tool_requests.append(("get_patient_appointments", {}))

        if any(word in normalized_message for word in ["slot", "available", "appointment", "schedule", "book"]):
            tool_requests.append(("get_available_slots", {"reason": user_message}))

        if any(word in normalized_message for word in ["book", "reserve", "confirm"]):
            tool_requests.append(("book_appointment", {"slot_id": user_message}))

        if "cancel" in normalized_message:
            tool_requests.append(("cancel_patient_appointment", {"appointment_id": user_message}))

        if any(word in normalized_message for word in ["location", "address", "directions"]):
            tool_requests.append(("get_location_details", {"location_id": "main-clinic"}))

        if any(word in normalized_message for word in ["human", "person", "representative"]):
            tool_requests.append(("handoff_to_human", {"reason": user_message}))

        results: list[ToolResultResponse] = []
        for tool_name, arguments in tool_requests:
            if tool_name not in self.enabled_tools:
                continue
            result = await self._execute_tool(
                session_id,
                ToolCallRequest(name=tool_name, arguments=arguments),
            )
            results.append(ToolResultResponse(name=tool_name, result=result))
        return results

    async def _generate_response(
        self,
        session_id: str,
        messages: list[dict],
        tool_results: list[ToolResultResponse],
    ) -> str:
        if self.llm_provider.supports_tool_calling and tool_results:
            return await self.llm_provider.generate_after_tools(
                messages=messages,
                assistant_message=getattr(self, "_last_assistant_tool_message", None),
                tool_messages=getattr(self, "_last_tool_messages", []),
            )
        if self.llm_provider.supports_tool_calling:
            direct_message = getattr(self, "_last_direct_provider_message", None)
            if direct_message:
                return direct_message
        return await self.llm_provider.generate(
            messages=self._build_messages(session_id),
            tool_results=[result.model_dump() for result in tool_results],
        )

    async def _execute_tool(self, session_id: str, tool_call: ToolCallRequest) -> dict:
        return await self.tool_client.call_tool(
            name=tool_call.name,
            arguments=tool_call.arguments,
            session_id=session_id,
        )

    @staticmethod
    def _slot_index_from_text(value: str) -> int | None:
        normalized = value.lower()
        ordinal_indexes = {
            "second": 1,
            "2": 1,
            "two": 1,
            "first": 0,
            "1": 0,
            "one": 0,
        }
        for keyword, index in ordinal_indexes.items():
            if re.search(rf"\b{keyword}\b", normalized):
                return index
        return None

    @staticmethod
    def _extract_validation_arguments(user_message: str) -> dict:
        dob_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", user_message)
        date_of_birth = dob_match.group(0) if dob_match else ""
        full_name = user_message
        if dob_match:
            full_name = user_message[: dob_match.start()]
        full_name = (
            full_name.replace("My name is", "")
            .replace("my name is", "")
            .replace("DOB", "")
            .replace("dob", "")
            .replace("date of birth", "")
            .strip(" ,.")
        )
        return {"full_name": full_name, "date_of_birth": date_of_birth}

    def _build_messages(self, session_id: str) -> list[dict]:
        messages = [{"role": "system", "content": build_system_prompt()}]
        for message in self.memory.get_messages(session_id):
            if message.role == "tool":
                messages.append(
                    {
                        "role": "system",
                        "content": f"Previous local tool result: {message.content}",
                    }
                )
            else:
                messages.append(message.model_dump())
        return messages
