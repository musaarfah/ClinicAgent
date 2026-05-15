from datetime import date, datetime

from clinic_agent.db.models import AppointmentSlot, Patient
from clinic_agent.db.session import session_scope


PATIENTS = [
    Patient(
        id="patient-001",
        full_name="Jamie Rivera",
        date_of_birth=date(1990, 1, 1),
        phone="555-0101",
    ),
    Patient(
        id="patient-002",
        full_name="Taylor Morgan",
        date_of_birth=date(1985, 5, 12),
        phone="555-0102",
    ),
]

SLOTS = [
    AppointmentSlot(
        id="slot-001",
        provider="Dr. Lee",
        starts_at=datetime.fromisoformat("2026-06-02T09:30:00"),
        location="Main Clinic",
        reason="checkup",
        is_available=True,
    ),
    AppointmentSlot(
        id="slot-002",
        provider="Dr. Patel",
        starts_at=datetime.fromisoformat("2026-06-03T14:00:00"),
        location="North Clinic",
        reason="checkup",
        is_available=True,
    ),
    AppointmentSlot(
        id="slot-003",
        provider="Dr. Brooks",
        starts_at=datetime.fromisoformat("2026-06-04T10:15:00"),
        location="Main Clinic",
        reason="lower back pain",
        is_available=True,
    ),
    AppointmentSlot(
        id="slot-004",
        provider="Dr. Chen",
        starts_at=datetime.fromisoformat("2026-06-05T11:00:00"),
        location="North Clinic",
        reason="general appointment",
        is_available=True,
    ),
]


def seed() -> None:
    with session_scope() as session:
        for patient in PATIENTS:
            session.merge(patient)
        for slot in SLOTS:
            session.merge(slot)


if __name__ == "__main__":
    seed()
    print("Seeded ClinicAgent database.")
