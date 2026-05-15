import pytest

from clinic_agent.agent.skills import tools_for_skills
from clinic_agent.db.repository import ClinicRepository
from clinic_agent.tools.registry import default_tool_registry


def test_registry_runs_db_backed_tool(clinic_repository: ClinicRepository) -> None:
    registry = default_tool_registry(clinic_repository)

    result = registry.run("get_available_slots", {"reason": "checkup"})

    assert result["slots"]


def test_registry_rejects_unknown_tool(clinic_repository: ClinicRepository) -> None:
    registry = default_tool_registry(clinic_repository)

    with pytest.raises(ValueError):
        registry.run("missing_tool", {})


def test_skill_mapping_filters_tools() -> None:
    assert tools_for_skills(["handoff"]) == ["handoff_to_human"]


def test_validate_patient_succeeds(clinic_repository: ClinicRepository) -> None:
    registry = default_tool_registry(clinic_repository)

    result = registry.run(
        "validate_patient",
        {"full_name": "Jamie Rivera", "date_of_birth": "1990-01-01"},
    )

    assert result["status"] == "validated"
    assert result["patient"]["id"] == "patient-001"


def test_validate_patient_accepts_natural_dob_format(clinic_repository: ClinicRepository) -> None:
    registry = default_tool_registry(clinic_repository)

    result = registry.run(
        "validate_patient",
        {"full_name": "Jamie Rivera", "date_of_birth": "1 January 1990"},
    )

    assert result["status"] == "validated"
    assert result["patient"]["id"] == "patient-001"


def test_validate_patient_requires_full_name(clinic_repository: ClinicRepository) -> None:
    registry = default_tool_registry(clinic_repository)

    result = registry.run(
        "validate_patient",
        {"full_name": "Jamie", "date_of_birth": "1990-01-01"},
    )

    assert result["status"] == "full_name_required"


def test_validate_patient_fails_for_wrong_dob(clinic_repository: ClinicRepository) -> None:
    registry = default_tool_registry(clinic_repository)

    result = registry.run(
        "validate_patient",
        {"full_name": "Jamie Rivera", "date_of_birth": "1999-01-01"},
    )

    assert result["status"] == "phone_required"


def test_validate_patient_can_fallback_to_phone(clinic_repository: ClinicRepository) -> None:
    registry = default_tool_registry(clinic_repository)

    result = registry.run(
        "validate_patient",
        {
            "full_name": "Jamie River",
            "date_of_birth": "1990-01-01",
            "phone": "555-0101",
        },
    )

    assert result["status"] == "validated"
    assert result["patient"]["id"] == "patient-001"


def test_patient_appointment_lookup_and_cancellation(clinic_repository: ClinicRepository) -> None:
    registry = default_tool_registry(clinic_repository)

    booking = registry.run(
        "book_appointment",
        {"patient_id": "patient-001", "slot_id": "slot-001"},
    )
    appointments = registry.run("get_patient_appointments", {"patient_id": "patient-001"})

    assert appointments["appointments"][0]["appointment_id"] == booking["appointment_id"]

    cancellation = registry.run(
        "cancel_patient_appointment",
        {"patient_id": "patient-001", "appointment_id": booking["appointment_id"]},
    )

    assert cancellation["status"] == "cancelled"
    available_slots = registry.run("get_available_slots", {"reason": "checkup"})
    assert any(slot["id"] == "slot-001" for slot in available_slots["slots"])
