from clinic_agent.tools.base import Tool
from clinic_agent.db.repository import ClinicRepository


class PatientSearchTool(Tool):
    name = "patient_search"
    description = "Search fictional local patients by name or free-text query."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Patient name or free-text search query.",
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def __init__(self, repository: ClinicRepository) -> None:
        self.repository = repository

    def run(self, arguments: dict) -> dict:
        query = str(arguments.get("query", ""))
        return {"matches": self.repository.search_patients(query)}


class ValidatePatientTool(Tool):
    name = "validate_patient"
    description = (
        "Validate a patient by full first and last name plus date of birth. "
        "Use phone only after name and date of birth do not find a match."
    )
    parameters = {
        "type": "object",
        "properties": {
            "full_name": {
                "type": "string",
                "description": "The patient's full first and last name.",
            },
            "date_of_birth": {
                "type": "string",
                "description": "The patient's date of birth, such as 1990-01-01 or 1 January 1990.",
            },
            "phone": {
                "type": "string",
                "description": "Optional phone number. Ask for this only after name and DOB fail.",
            },
        },
        "required": ["full_name", "date_of_birth"],
        "additionalProperties": False,
    }

    def __init__(self, repository: ClinicRepository) -> None:
        self.repository = repository

    def run(self, arguments: dict) -> dict:
        try:
            return self.repository.validate_patient(
                full_name=str(arguments.get("full_name", "")),
                date_of_birth=str(arguments.get("date_of_birth", "")),
                phone=str(arguments.get("phone", "")) or None,
            )
        except ValueError:
            return {
                "status": "invalid_date_of_birth",
                "message": "Ask for the date of birth again. Formats like 1990-01-01 or 1 January 1990 are supported.",
            }


class GetAvailableSlotsTool(Tool):
    name = "get_available_slots"
    description = "Return fictional available appointment slots for a visit reason."
    parameters = {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "The user's appointment reason or scheduling request.",
            }
        },
        "required": ["reason"],
        "additionalProperties": False,
    }

    def __init__(self, repository: ClinicRepository) -> None:
        self.repository = repository

    def run(self, arguments: dict) -> dict:
        reason = str(arguments.get("reason", "general visit"))
        return {"reason": reason, "slots": self.repository.get_available_slots(reason)}


class BookAppointmentTool(Tool):
    name = "book_appointment"
    description = "Book a fictional appointment by slot ID."
    parameters = {
        "type": "object",
        "properties": {
            "slot_id": {
                "type": "string",
                "description": "The slot ID to book, such as slot-001.",
            }
        },
        "required": ["slot_id"],
        "additionalProperties": False,
    }

    def __init__(self, repository: ClinicRepository) -> None:
        self.repository = repository

    def run(self, arguments: dict) -> dict:
        return self.repository.book_appointment(
            patient_id=str(arguments.get("patient_id", "")),
            slot_id=str(arguments.get("slot_id", "")),
        )


class GetPatientAppointmentsTool(Tool):
    name = "get_patient_appointments"
    description = "List appointments for the validated fictional patient."
    parameters = {
        "type": "object",
        "properties": {
            "patient_id": {
                "type": "string",
                "description": "The validated patient ID.",
            }
        },
        "required": ["patient_id"],
        "additionalProperties": False,
    }

    def __init__(self, repository: ClinicRepository) -> None:
        self.repository = repository

    def run(self, arguments: dict) -> dict:
        return {
            "appointments": self.repository.get_patient_appointments(
                patient_id=str(arguments.get("patient_id", ""))
            )
        }


class CancelPatientAppointmentTool(Tool):
    name = "cancel_patient_appointment"
    description = "Cancel one appointment for the validated fictional patient."
    parameters = {
        "type": "object",
        "properties": {
            "patient_id": {
                "type": "string",
                "description": "The validated patient ID.",
            },
            "appointment_id": {
                "type": "string",
                "description": "The appointment ID to cancel.",
            },
        },
        "required": ["patient_id", "appointment_id"],
        "additionalProperties": False,
    }

    def __init__(self, repository: ClinicRepository) -> None:
        self.repository = repository

    def run(self, arguments: dict) -> dict:
        return self.repository.cancel_patient_appointment(
            patient_id=str(arguments.get("patient_id", "")),
            appointment_id=str(arguments.get("appointment_id", "")),
        )


class GetLocationDetailsTool(Tool):
    name = "get_location_details"
    description = "Return fictional clinic address and hours."
    parameters = {
        "type": "object",
        "properties": {
            "location_id": {
                "type": "string",
                "description": "The clinic location ID. Use main-clinic if unknown.",
            }
        },
        "required": ["location_id"],
        "additionalProperties": False,
    }

    def run(self, arguments: dict) -> dict:
        return {
            "location_id": arguments.get("location_id", "main-clinic"),
            "name": "Main Clinic",
            "address": "100 Wellness Ave, Springfield",
            "hours": "Mon-Fri 8:00 AM - 5:00 PM",
        }


class HandoffToHumanTool(Tool):
    name = "handoff_to_human"
    description = "Create a fictional handoff request when the user wants a human."
    parameters = {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Why the user needs a human representative.",
            }
        },
        "required": ["reason"],
        "additionalProperties": False,
    }

    def run(self, arguments: dict) -> dict:
        return {
            "status": "handoff_requested",
            "reason": arguments.get("reason", "Patient requested a human representative."),
        }
