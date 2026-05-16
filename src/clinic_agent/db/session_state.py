from collections.abc import Callable

from clinic_agent.db.models import AgentSessionState
from clinic_agent.db.session import session_scope


SessionProvider = Callable[[], object]


class AgentSessionStateRepository:
    def __init__(self, session_provider: SessionProvider = session_scope) -> None:
        self.session_provider = session_provider

    def create_session(self, session_id: str) -> dict:
        with self.session_provider() as session:
            state = session.get(AgentSessionState, session_id)
            if not state:
                state = AgentSessionState(
                    session_id=session_id,
                    last_available_slots=[],
                    last_patient_appointments=[],
                )
                session.add(state)
                session.flush()
            return self._state_to_dict(state)

    def get_state(self, session_id: str) -> dict:
        with self.session_provider() as session:
            state = self._get_or_create_state(session, session_id)
            return self._state_to_dict(state)

    def set_validated_patient(self, session_id: str, patient: dict) -> dict:
        with self.session_provider() as session:
            state = self._get_or_create_state(session, session_id)
            state.validated_patient_id = patient["id"]
            state.validated_patient = patient
            session.flush()
            return self._state_to_dict(state)

    def set_last_available_slots(self, session_id: str, slots: list[dict]) -> dict:
        return self._update_json_field(session_id, "last_available_slots", slots)

    def set_last_patient_appointments(self, session_id: str, appointments: list[dict]) -> dict:
        return self._update_json_field(session_id, "last_patient_appointments", appointments)

    def set_last_booked_appointment(self, session_id: str, appointment: dict) -> dict:
        return self._update_json_field(session_id, "last_booked_appointment", appointment)

    def set_last_cancelled_appointment(self, session_id: str, appointment: dict) -> dict:
        return self._update_json_field(session_id, "last_cancelled_appointment", appointment)

    def _update_json_field(self, session_id: str, field_name: str, value: dict | list) -> dict:
        with self.session_provider() as session:
            state = self._get_or_create_state(session, session_id)
            setattr(state, field_name, value)
            session.flush()
            return self._state_to_dict(state)

    @staticmethod
    def _get_or_create_state(session, session_id: str) -> AgentSessionState:
        state = session.get(AgentSessionState, session_id)
        if state:
            return state

        state = AgentSessionState(
            session_id=session_id,
            last_available_slots=[],
            last_patient_appointments=[],
        )
        session.add(state)
        session.flush()
        return state

    @staticmethod
    def _state_to_dict(state: AgentSessionState) -> dict:
        return {
            "session_id": state.session_id,
            "validated_patient_id": state.validated_patient_id,
            "validated_patient": state.validated_patient,
            "last_available_slots": state.last_available_slots or [],
            "last_patient_appointments": state.last_patient_appointments or [],
            "last_booked_appointment": state.last_booked_appointment,
            "last_cancelled_appointment": state.last_cancelled_appointment,
        }
