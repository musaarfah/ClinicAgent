import os

from clinic_agent.llm.base import LlmProvider


class GeminiProvider(LlmProvider):
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    async def generate(self, messages: list[dict[str, str]], tool_results: list[dict]) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = self._to_prompt(messages, tool_results)
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response.text or ""

    @staticmethod
    def _to_prompt(messages: list[dict[str, str]], tool_results: list[dict]) -> str:
        lines = [f"{message['role']}: {message['content']}" for message in messages]
        if tool_results:
            lines.append(f"tool_results: {tool_results}")
        return "\n".join(lines)

