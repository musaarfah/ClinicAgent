from collections.abc import Callable
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import select

from clinic_agent.db.models import Appointment, AppointmentSlot, Patient
from clinic_agent.db.session import session_scope


SessionProvider = Callable[[], object]


class ClinicRepository:
    def __init__(self, session_provider: SessionProvider = session_scope) -> None:
        self.session_provider = session_provider

    def search_patients(self, query: str) -> list[dict]:
        normalized_query = query.strip().lower()
        with self.session_provider() as session:
            patients = session.scalars(select(Patient).order_by(Patient.full_name)).all()
            matches = [
                self._patient_to_dict(patient)
                for patient in patients
                if normalized_query in patient.full_name.lower()
            ]
        return matches

    def validate_patient(self, full_name: str, date_of_birth: str, phone: str | None = None) -> dict:
        parsed_dob = parse_date_of_birth(date_of_birth)
        normalized_name = " ".join(full_name.lower().split())
        if len(normalized_name.split()) < 2:
            return {
                "status": "full_name_required",
                "message": "Please provide the patient's full first and last name.",
            }

        normalized_phone = normalize_phone(phone or "")
        with self.session_provider() as session:
            patients = session.scalars(select(Patient)).all()
            patient = next(
                (
                    item
                    for item in patients
                    if " ".join(item.full_name.lower().split()) == normalized_name
                    and item.date_of_birth == parsed_dob
                ),
                None,
            )

            if not patient and normalized_phone:
                patient = next(
                    (
                        item
                        for item in patients
                        if item.date_of_birth == parsed_dob
                        and normalize_phone(item.phone or "") == normalized_phone
                    ),
                    None,
                )

        if not patient:
            if not normalized_phone:
                return {
                    "status": "phone_required",
                    "message": "No exact match was found. Ask for the patient's phone number to verify.",
                }
            return {"status": "validation_failed"}
        return {"status": "validated", "patient": self._patient_to_dict(patient)}

    def get_available_slots(self, reason: str) -> list[dict]:
        with self.session_provider() as session:
            slots = session.scalars(
                select(AppointmentSlot)
                .where(AppointmentSlot.is_available.is_(True))
                .order_by(AppointmentSlot.starts_at)
            ).all()
            return [self._slot_to_dict(slot) for slot in slots]

    def book_appointment(self, patient_id: str, slot_id: str) -> dict:
        with self.session_provider() as session:
            patient = session.get(Patient, patient_id)
            slot = session.get(AppointmentSlot, slot_id)
            if not patient:
                return {"status": "patient_not_found", "patient_id": patient_id}
            if not slot:
                return {"status": "slot_not_found", "slot_id": slot_id}
            if not slot.is_available:
                return {"status": "slot_unavailable", "slot": self._slot_to_dict(slot)}

            appointment = Appointment(
                id=f"appt-{uuid4().hex[:8]}",
                patient_id=patient.id,
                slot_id=slot.id,
                status="booked",
            )
            slot.is_available = False
            session.add(appointment)
            session.flush()
            return {
                "appointment_id": appointment.id,
                "status": appointment.status,
                "patient": self._patient_to_dict(patient),
                "slot": self._slot_to_dict(slot),
            }

    def get_patient_appointments(self, patient_id: str) -> list[dict]:
        with self.session_provider() as session:
            appointments = session.scalars(
                select(Appointment)
                .where(Appointment.patient_id == patient_id)
                .order_by(Appointment.created_at)
            ).all()
            return [self._appointment_to_dict(appointment) for appointment in appointments]

    def cancel_patient_appointment(self, patient_id: str, appointment_id: str) -> dict:
        with self.session_provider() as session:
            appointment = session.get(Appointment, appointment_id)
            if not appointment:
                return {"status": "appointment_not_found", "appointment_id": appointment_id}
            if appointment.patient_id != patient_id:
                return {
                    "status": "appointment_not_found",
                    "appointment_id": appointment_id,
                    "message": "No matching appointment was found for the validated patient.",
                }
            appointment.status = "cancelled"
            appointment.slot.is_available = True
            return self._appointment_to_dict(appointment)

    @staticmethod
    def _patient_to_dict(patient: Patient) -> dict:
        return {
            "id": patient.id,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth.isoformat(),
            "phone": patient.phone,
        }

    @staticmethod
    def _slot_to_dict(slot: AppointmentSlot) -> dict:
        return {
            "id": slot.id,
            "provider": slot.provider,
            "time": slot.starts_at.isoformat(),
            "location": slot.location,
            "reason": slot.reason,
            "is_available": slot.is_available,
        }

    def _appointment_to_dict(self, appointment: Appointment) -> dict:
        return {
            "appointment_id": appointment.id,
            "status": appointment.status,
            "patient": self._patient_to_dict(appointment.patient),
            "slot": self._slot_to_dict(appointment.slot),
        }


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def parse_date_of_birth(value: str) -> date:
    normalized_value = " ".join(value.strip().replace(",", "").split())
    date_formats = (
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%d %B %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%b %d %Y",
    )
    for date_format in date_formats:
        try:
            return datetime.strptime(normalized_value, date_format).date()
        except ValueError:
            continue
    raise ValueError("Unsupported date of birth format")


def normalize_phone(value: str) -> str:
    return "".join(character for character in value if character.isdigit())
