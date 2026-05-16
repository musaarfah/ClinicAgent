from fastapi.testclient import TestClient

from clinic_agent.api import routes
from clinic_agent.db.repository import ClinicRepository
from clinic_agent.db.session_state import AgentSessionStateRepository
from clinic_agent.main import create_app
from clinic_agent.memory.store import memory_store
from conftest import InProcessMcpToolClient


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_returns_session_and_message(sqlite_database_url: str, monkeypatch) -> None:
    memory_store.clear()
    monkeypatch.setattr(
        routes,
        "create_tool_client",
        lambda: InProcessMcpToolClient(
            ClinicRepository(),
            AgentSessionStateRepository(),
        ),
    )
    client = TestClient(create_app())

    response = client.post(
        "/api/chat",
        json={"message": "I need to book an appointment", "provider": "fake"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["message"]
    assert payload["tool_results"]


def test_create_session_returns_backend_greeting(sqlite_database_url: str) -> None:
    memory_store.clear()
    client = TestClient(create_app())

    response = client.post("/api/sessions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["messages"][0]["role"] == "assistant"
    assert "ClinicAgent" in payload["messages"][0]["content"]


def test_created_sessions_are_isolated(sqlite_database_url: str) -> None:
    memory_store.clear()
    client = TestClient(create_app())

    first_session = client.post("/api/sessions").json()
    second_session = client.post("/api/sessions").json()

    assert first_session["session_id"] != second_session["session_id"]
    assert len(memory_store.get_messages(first_session["session_id"])) == 1
    assert len(memory_store.get_messages(second_session["session_id"])) == 1
