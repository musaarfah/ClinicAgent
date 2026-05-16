from clinic_agent.db.repository import ClinicRepository
from clinic_agent_mcp.tools.dependencies import clinic_repository


def get_location_details(
    location_id: str = "main-clinic",
    repository: ClinicRepository = clinic_repository,
) -> dict:
    return repository.get_location_details(location_id)
