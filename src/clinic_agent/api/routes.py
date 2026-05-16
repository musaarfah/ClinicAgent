from uuid import uuid4

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from clinic_agent.agent.orchestrator import AgentOrchestrator
from clinic_agent.api.schemas import ChatRequest, ChatResponse, SessionResponse
from clinic_agent.db.session import session_scope
from clinic_agent.db.session_state import AgentSessionStateRepository
from clinic_agent.llm.factory import create_llm_provider
from clinic_agent.memory.store import memory_store
from clinic_agent.tools.client import create_tool_client

router = APIRouter()

SESSION_GREETING = (
    "Hi, I’m ClinicAgent. I can help you find available appointments, validate a "
    "fictional patient, book a visit, view appointments, or cancel one. What can I "
    "help you with today?"
)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
async def database_health() -> dict[str, str]:
    try:
        with session_scope() as session:
            session.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(status_code=503, detail="database unavailable") from error
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        orchestrator = AgentOrchestrator(
            llm_provider=create_llm_provider(request.provider),
            memory=memory_store,
            tool_client=create_tool_client(),
        )
        return await orchestrator.handle_message(
            user_message=request.message,
            session_id=request.session_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/sessions", response_model=SessionResponse)
async def create_session() -> SessionResponse:
    session_id = str(uuid4())
    AgentSessionStateRepository().create_session(session_id)
    memory_store.add_message(session_id, "assistant", SESSION_GREETING)
    return SessionResponse(
        session_id=session_id,
        messages=[message.model_dump() for message in memory_store.get_messages(session_id)],
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    return SessionResponse(
        session_id=session_id,
        messages=[message.model_dump() for message in memory_store.get_messages(session_id)],
    )
