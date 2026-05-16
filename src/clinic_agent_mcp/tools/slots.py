from clinic_agent.db.repository import ClinicRepository
from clinic_agent.db.session_state import AgentSessionStateRepository
from clinic_agent_mcp.tools.dependencies import clinic_repository, session_state_repository


def get_available_slots(
    session_id: str,
    reason: str,
    repository: ClinicRepository = clinic_repository,
    state_repository: AgentSessionStateRepository = session_state_repository,
) -> dict:
    slots = repository.get_available_slots(reason)
    state_repository.set_last_available_slots(session_id, slots)
    return {"reason": reason, "slots": slots}
