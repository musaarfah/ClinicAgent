from clinic_agent.tools.base import Tool
from clinic_agent.db.repository import ClinicRepository
from clinic_agent.tools.scheduling import (
    BookAppointmentTool,
    CancelPatientAppointmentTool,
    GetAvailableSlotsTool,
    GetLocationDetailsTool,
    GetPatientAppointmentsTool,
    HandoffToHumanTool,
    PatientSearchTool,
    ValidatePatientTool,
)


class ToolRegistry:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def names(self) -> list[str]:
        return sorted(self._tools)

    def openai_definitions(self, allowed_tool_names: list[str]) -> list[dict]:
        allowed = set(allowed_tool_names)
        return [
            tool.openai_definition()
            for tool in self._tools.values()
            if tool.name in allowed
        ]

    def run(self, name: str, arguments: dict) -> dict:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name].run(arguments)


def default_tool_registry(repository: ClinicRepository | None = None) -> ToolRegistry:
    clinic_repository = repository or ClinicRepository()
    return ToolRegistry(
        [
            PatientSearchTool(clinic_repository),
            ValidatePatientTool(clinic_repository),
            GetAvailableSlotsTool(clinic_repository),
            BookAppointmentTool(clinic_repository),
            GetPatientAppointmentsTool(clinic_repository),
            CancelPatientAppointmentTool(clinic_repository),
            GetLocationDetailsTool(),
            HandoffToHumanTool(),
        ]
    )
