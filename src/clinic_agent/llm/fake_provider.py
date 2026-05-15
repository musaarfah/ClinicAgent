from clinic_agent.llm.base import LlmProvider


class FakeProvider(LlmProvider):
    async def generate(self, messages: list[dict[str, str]], tool_results: list[dict]) -> str:
        if tool_results:
            tool_names = ", ".join(result["name"] for result in tool_results)
            return f"I checked the clinic tools ({tool_names}) and found options for you."
        return "I can help with appointment scheduling, cancellations, clinic details, or handoff."

