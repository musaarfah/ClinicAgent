from uuid import uuid4

from sqlalchemy import select

from clinic_agent.agent.skills import tools_for_skills
from clinic_agent.db.models import HandoffRequest
from clinic_agent.db.repository import ClinicRepository
from clinic_agent.db.session_state import AgentSessionStateRepository
from clinic_agent_mcp.tools.appointments import (
    book_appointment,
    cancel_patient_appointment,
    get_patient_appointments,
)
from clinic_agent_mcp.tools.handoff import handoff_to_human
from clinic_agent_mcp.tools.locations import get_location_details
from clinic_agent_mcp.tools.patients import validate_patient
from clinic_agent_mcp.tools.slots import get_available_slots


def test_skill_mapping_filters_tools() -> None:
    assert tools_for_skills(["handoff"]) == ["handoff_to_human"]


def test_validate_patient_succeeds(
    clinic_repository: ClinicRepository,
    agent_session_state_repository: AgentSessionStateRepository,
) -> None:
    result = validate_patient(
        session_id=str(uuid4()),
        full_name="Jamie Rivera",
        date_of_birth="1990-01-01",
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )

    assert result["status"] == "validated"
    assert result["patient"]["id"] == "patient-001"


def test_validate_patient_accepts_natural_dob_format(
    clinic_repository: ClinicRepository,
    agent_session_state_repository: AgentSessionStateRepository,
) -> None:
    result = validate_patient(
        session_id=str(uuid4()),
        full_name="Jamie Rivera",
        date_of_birth="1 January 1990",
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )

    assert result["status"] == "validated"
    assert result["patient"]["id"] == "patient-001"


def test_validate_patient_requires_full_name(
    clinic_repository: ClinicRepository,
    agent_session_state_repository: AgentSessionStateRepository,
) -> None:
    result = validate_patient(
        session_id=str(uuid4()),
        full_name="Jamie",
        date_of_birth="1990-01-01",
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )

    assert result["status"] == "full_name_required"


def test_validate_patient_can_fallback_to_phone(
    clinic_repository: ClinicRepository,
    agent_session_state_repository: AgentSessionStateRepository,
) -> None:
    result = validate_patient(
        session_id=str(uuid4()),
        full_name="Jamie River",
        date_of_birth="1990-01-01",
        phone="555-0101",
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )

    assert result["status"] == "validated"
    assert result["patient"]["id"] == "patient-001"


def test_patient_appointment_lookup_and_cancellation(
    clinic_repository: ClinicRepository,
    agent_session_state_repository: AgentSessionStateRepository,
) -> None:
    session_id = str(uuid4())
    validate_patient(
        session_id=session_id,
        full_name="Jamie Rivera",
        date_of_birth="1990-01-01",
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )
    get_available_slots(
        session_id=session_id,
        reason="checkup",
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )

    booking = book_appointment(
        session_id=session_id,
        slot_id="first",
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )
    appointments = get_patient_appointments(
        session_id=session_id,
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )

    assert appointments["appointments"][0]["appointment_id"] == booking["appointment_id"]

    cancellation = cancel_patient_appointment(
        session_id=session_id,
        appointment_id=booking["appointment_id"],
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )

    assert cancellation["status"] == "cancelled"
    available_slots = get_available_slots(
        session_id=session_id,
        reason="checkup",
        repository=clinic_repository,
        state_repository=agent_session_state_repository,
    )
    assert any(slot["id"] == "slot-001" for slot in available_slots["slots"])


def test_location_lookup_reads_from_database(clinic_repository: ClinicRepository) -> None:
    result = get_location_details("north-clinic", repository=clinic_repository)

    assert result["location_id"] == "north-clinic"
    assert result["name"] == "North Clinic"


def test_handoff_request_is_persisted(
    clinic_repository: ClinicRepository,
    sqlite_database_url: str,
) -> None:
    session_id = str(uuid4())

    result = handoff_to_human(
        session_id=session_id,
        reason="Need a human",
        repository=clinic_repository,
    )

    assert result["status"] == "queued"

    with clinic_repository.session_provider() as session:
        handoff_request = session.scalar(
            select(HandoffRequest).where(HandoffRequest.id == result["handoff_id"])
        )
        assert handoff_request is not None
        assert handoff_request.session_id == session_id
