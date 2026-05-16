from clinic_agent.db.repository import ClinicRepository
from clinic_agent.db.session_state import AgentSessionStateRepository
from clinic_agent_mcp.tools.dependencies import clinic_repository, session_state_repository


def patient_search(
    query: str,
    repository: ClinicRepository = clinic_repository,
) -> dict:
    return {"matches": repository.search_patients(query)}


def validate_patient(
    session_id: str,
    full_name: str,
    date_of_birth: str,
    phone: str | None = None,
    repository: ClinicRepository = clinic_repository,
    state_repository: AgentSessionStateRepository = session_state_repository,
) -> dict:
    try:
        result = repository.validate_patient(
            full_name=full_name,
            date_of_birth=date_of_birth,
            phone=phone,
        )
    except ValueError:
        return {
            "status": "invalid_date_of_birth",
            "message": "Ask for the date of birth again. Formats like 1990-01-01 or 1 January 1990 are supported.",
        }

    if result.get("status") == "validated":
        state_repository.set_validated_patient(session_id, result["patient"])
    return result
