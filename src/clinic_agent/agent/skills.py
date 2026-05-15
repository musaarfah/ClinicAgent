from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    tools: tuple[str, ...]


SKILLS: tuple[Skill, ...] = (
    Skill(
        name="appointment_scheduling",
        tools=(
            "patient_search",
            "validate_patient",
            "get_available_slots",
            "book_appointment",
            "get_patient_appointments",
            "cancel_patient_appointment",
            "get_location_details",
        ),
    ),
    Skill(name="handoff", tools=("handoff_to_human",)),
)


def tools_for_skills(skill_names: list[str]) -> list[str]:
    selected = set(skill_names)
    tool_names: list[str] = []
    for skill in SKILLS:
        if skill.name in selected:
            tool_names.extend(skill.tools)
    return list(dict.fromkeys(tool_names))
