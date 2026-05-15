from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    provider: str | None = Field(default=None, pattern="^(fake|openai|gemini)$")


class ToolResultResponse(BaseModel):
    name: str
    result: dict


class ChatResponse(BaseModel):
    session_id: str
    message: str
    tool_results: list[ToolResultResponse] = []


class SessionResponse(BaseModel):
    session_id: str
    messages: list[dict[str, str]]
