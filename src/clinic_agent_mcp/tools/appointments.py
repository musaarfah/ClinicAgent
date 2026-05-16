from clinic_agent.db.repository import ClinicRepository
from clinic_agent.db.session_state import AgentSessionStateRepository
from clinic_agent_mcp.tools.dependencies import clinic_repository, session_state_repository
from clinic_agent_mcp.tools.references import resolve_reference


def book_appointment(
    session_id: str,
    slot_id: str,
    repository: ClinicRepository = clinic_repository,
    state_repository: AgentSessionStateRepository = session_state_repository,
) -> dict:
    validation_error = validation_required(session_id, state_repository)
    if validation_error:
        return validation_error

    state = state_repository.get_state(session_id)
    resolved_slot_id = resolve_reference(slot_id, state["last_available_slots"], "id")
    result = repository.book_appointment(
        patient_id=state["validated_patient_id"],
        slot_id=resolved_slot_id,
    )
    if result.get("status") == "booked":
        state_repository.set_last_booked_appointment(session_id, result)
    return result


def get_patient_appointments(
    session_id: str,
    repository: ClinicRepository = clinic_repository,
    state_repository: AgentSessionStateRepository = session_state_repository,
) -> dict:
    validation_error = validation_required(session_id, state_repository)
    if validation_error:
        return validation_error

    state = state_repository.get_state(session_id)
    appointments = repository.get_patient_appointments(state["validated_patient_id"])
    state_repository.set_last_patient_appointments(session_id, appointments)
    return {"appointments": appointments}


def cancel_patient_appointment(
    session_id: str,
    appointment_id: str,
    repository: ClinicRepository = clinic_repository,
    state_repository: AgentSessionStateRepository = session_state_repository,
) -> dict:
    validation_error = validation_required(session_id, state_repository)
    if validation_error:
        return validation_error

    state = state_repository.get_state(session_id)
    resolved_appointment_id = resolve_reference(
        appointment_id,
        state["last_patient_appointments"],
        "appointment_id",
    )
    result = repository.cancel_patient_appointment(
        patient_id=state["validated_patient_id"],
        appointment_id=resolved_appointment_id,
    )
    if result.get("status") == "cancelled":
        state_repository.set_last_cancelled_appointment(session_id, result)
    return result


def validation_required(
    session_id: str,
    state_repository: AgentSessionStateRepository,
) -> dict | None:
    state = state_repository.get_state(session_id)
    if state.get("validated_patient_id"):
        return None
    return {
        "status": "validation_required",
        "message": "Ask the user for their full name and date of birth before managing appointments.",
    }
