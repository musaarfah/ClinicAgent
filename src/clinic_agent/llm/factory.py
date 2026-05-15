import os

from clinic_agent.llm.base import LlmProvider
from clinic_agent.llm.fake_provider import FakeProvider
from clinic_agent.llm.gemini_provider import GeminiProvider
from clinic_agent.llm.openai_provider import OpenAiProvider


def create_llm_provider(provider_name: str | None = None) -> LlmProvider:
    provider = (provider_name or os.getenv("LLM_PROVIDER", "fake")).lower()
    if provider == "openai":
        return OpenAiProvider()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "fake":
        return FakeProvider()
    raise ValueError(f"Unsupported LLM provider: {provider}")

