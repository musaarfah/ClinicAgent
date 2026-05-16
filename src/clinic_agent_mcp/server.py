import os

from mcp.server.fastmcp import FastMCP

from clinic_agent_mcp.tools.appointments import (
    book_appointment as book_appointment_tool,
)
from clinic_agent_mcp.tools.appointments import (
    cancel_patient_appointment as cancel_patient_appointment_tool,
)
from clinic_agent_mcp.tools.appointments import (
    get_patient_appointments as get_patient_appointments_tool,
)
from clinic_agent_mcp.tools.handoff import handoff_to_human as handoff_to_human_tool
from clinic_agent_mcp.tools.locations import get_location_details as get_location_details_tool
from clinic_agent_mcp.tools.patients import patient_search as patient_search_tool
from clinic_agent_mcp.tools.patients import validate_patient as validate_patient_tool
from clinic_agent_mcp.tools.slots import get_available_slots as get_available_slots_tool


mcp = FastMCP(
    "clinic-agent-tools",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "9100")),
    streamable_http_path=os.getenv("MCP_PATH", "/mcp"),
    json_response=True,
)


@mcp.tool()
def patient_search(query: str) -> dict:
    """Search fictional patients by name."""
    return patient_search_tool(query=query)


@mcp.tool()
def validate_patient(
    session_id: str,
    full_name: str,
    date_of_birth: str,
    phone: str | None = None,
) -> dict:
    """Validate a fictional patient using full name, date of birth, and optional phone."""
    return validate_patient_tool(
        session_id=session_id,
        full_name=full_name,
        date_of_birth=date_of_birth,
        phone=phone,
    )


@mcp.tool()
def get_available_slots(session_id: str, reason: str) -> dict:
    """Find available appointment slots for the requested visit reason."""
    return get_available_slots_tool(session_id=session_id, reason=reason)


@mcp.tool()
def book_appointment(session_id: str, slot_id: str) -> dict:
    """Book an appointment for the validated patient."""
    return book_appointment_tool(session_id=session_id, slot_id=slot_id)


@mcp.tool()
def get_patient_appointments(session_id: str) -> dict:
    """List appointments for the validated patient."""
    return get_patient_appointments_tool(session_id=session_id)


@mcp.tool()
def cancel_patient_appointment(session_id: str, appointment_id: str) -> dict:
    """Cancel an appointment for the validated patient."""
    return cancel_patient_appointment_tool(
        session_id=session_id,
        appointment_id=appointment_id,
    )


@mcp.tool()
def get_location_details(location_id: str = "main-clinic") -> dict:
    """Return basic fictional clinic location details."""
    return get_location_details_tool(location_id=location_id)


@mcp.tool()
def handoff_to_human(session_id: str, reason: str) -> dict:
    """Mock a handoff to a human clinic team member."""
    return handoff_to_human_tool(session_id=session_id, reason=reason)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
