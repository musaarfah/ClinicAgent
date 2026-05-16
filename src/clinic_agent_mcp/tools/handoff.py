from clinic_agent.db.repository import ClinicRepository
from clinic_agent_mcp.tools.dependencies import clinic_repository


def handoff_to_human(
    session_id: str,
    reason: str,
    repository: ClinicRepository = clinic_repository,
) -> dict:
    return repository.create_handoff_request(session_id=session_id, reason=reason)
