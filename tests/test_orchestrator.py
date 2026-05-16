import pytest

from clinic_agent.agent.orchestrator import AgentOrchestrator
from clinic_agent.llm.fake_provider import FakeProvider
from clinic_agent.memory.store import ConversationMemory
from clinic_agent.db.repository import ClinicRepository
from clinic_agent.db.session_state import AgentSessionStateRepository
from conftest import InProcessMcpToolClient


@pytest.mark.asyncio
async def test_orchestrator_uses_scheduling_tools(clinic_repository: ClinicRepository) -> None:
    state_repository = AgentSessionStateRepository(clinic_repository.session_provider)
    orchestrator = AgentOrchestrator(
        llm_provider=FakeProvider(),
        memory=ConversationMemory(),
        tool_client=InProcessMcpToolClient(clinic_repository, state_repository),
    )

    response = await orchestrator.handle_message("Can you find available appointment slots?")

    assert response.session_id
    assert response.tool_results[0].name == "patient_search"
    assert any(result.name == "get_available_slots" for result in response.tool_results)


@pytest.mark.asyncio
async def test_orchestrator_requires_validation_before_booking(
    clinic_repository: ClinicRepository,
) -> None:
    memory = ConversationMemory()
    state_repository = AgentSessionStateRepository(clinic_repository.session_provider)
    orchestrator = AgentOrchestrator(
        llm_provider=FakeProvider(),
        memory=memory,
        tool_client=InProcessMcpToolClient(clinic_repository, state_repository),
    )

    first_response = await orchestrator.handle_message("Show me available slots")
    second_response = await orchestrator.handle_message(
        "Book the second one",
        session_id=first_response.session_id,
    )

    booking_result = next(
        result for result in second_response.tool_results if result.name == "book_appointment"
    )
    assert booking_result.result["status"] == "validation_required"


@pytest.mark.asyncio
async def test_orchestrator_books_referenced_slot_after_validation(
    clinic_repository: ClinicRepository,
) -> None:
    memory = ConversationMemory()
    state_repository = AgentSessionStateRepository(clinic_repository.session_provider)
    orchestrator = AgentOrchestrator(
        llm_provider=FakeProvider(),
        memory=memory,
        tool_client=InProcessMcpToolClient(clinic_repository, state_repository),
    )

    first_response = await orchestrator.handle_message("Show me available slots")
    await orchestrator.handle_message(
        "My name is Jamie Rivera DOB 1990-01-01",
        session_id=first_response.session_id,
    )
    second_response = await orchestrator.handle_message(
        "Book the second one",
        session_id=first_response.session_id,
    )

    booking_result = next(
        result for result in second_response.tool_results if result.name == "book_appointment"
    )
    assert booking_result.result["slot"]["id"] == "slot-002"


@pytest.mark.asyncio
async def test_orchestrator_lists_and_cancels_patient_appointment(
    clinic_repository: ClinicRepository,
) -> None:
    memory = ConversationMemory()
    state_repository = AgentSessionStateRepository(clinic_repository.session_provider)
    orchestrator = AgentOrchestrator(
        llm_provider=FakeProvider(),
        memory=memory,
        tool_client=InProcessMcpToolClient(clinic_repository, state_repository),
    )

    first_response = await orchestrator.handle_message("Show me available slots")
    await orchestrator.handle_message(
        "My name is Jamie Rivera DOB 1990-01-01",
        session_id=first_response.session_id,
    )
    await orchestrator.handle_message(
        "Book the second one",
        session_id=first_response.session_id,
    )
    lookup_response = await orchestrator.handle_message(
        "What appointments do I have?",
        session_id=first_response.session_id,
    )
    cancellation_response = await orchestrator.handle_message(
        "Cancel the Dr. Patel appointment",
        session_id=first_response.session_id,
    )

    lookup_result = next(
        result for result in lookup_response.tool_results if result.name == "get_patient_appointments"
    )
    cancellation_result = next(
        result
        for result in cancellation_response.tool_results
        if result.name == "cancel_patient_appointment"
    )

    assert lookup_result.result["appointments"][0]["slot"]["id"] == "slot-002"
    assert cancellation_result.result["status"] == "cancelled"
    assert cancellation_result.result["slot"]["id"] == "slot-002"
