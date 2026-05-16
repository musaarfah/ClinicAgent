from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from clinic_agent.db.models import AppointmentSlot, Base, ClinicLocation, Patient
from clinic_agent.db.repository import ClinicRepository
from clinic_agent.db.session import reset_session_factory
from clinic_agent.db.session_state import AgentSessionStateRepository
from clinic_agent.memory.store import memory_store
from clinic_agent_mcp.tools.appointments import (
    book_appointment,
    cancel_patient_appointment,
    get_patient_appointments,
)
from clinic_agent_mcp.tools.handoff import handoff_to_human
from clinic_agent_mcp.tools.locations import get_location_details
from clinic_agent_mcp.tools.patients import patient_search, validate_patient
from clinic_agent_mcp.tools.slots import get_available_slots


@pytest.fixture()
def sqlite_database_url(tmp_path, monkeypatch) -> str:
    database_url = f"sqlite:///{tmp_path}/clinic_agent_test.db"
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_session_factory()

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    seed_test_database(session_factory)
    memory_store.clear()
    return database_url


@pytest.fixture()
def clinic_repository(sqlite_database_url: str) -> ClinicRepository:
    engine = create_engine(sqlite_database_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def session_provider() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return ClinicRepository(session_provider=session_provider)


@pytest.fixture()
def agent_session_state_repository(sqlite_database_url: str) -> AgentSessionStateRepository:
    engine = create_engine(sqlite_database_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def session_provider() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return AgentSessionStateRepository(session_provider=session_provider)


class InProcessMcpToolClient:
    def __init__(
        self,
        clinic_repository: ClinicRepository,
        session_state_repository: AgentSessionStateRepository,
    ) -> None:
        self.clinic_repository = clinic_repository
        self.session_state_repository = session_state_repository

    async def openai_definitions(self, allowed_tool_names: list[str]) -> list[dict]:
        return []

    async def call_tool(self, name: str, arguments: dict, session_id: str) -> dict:
        mcp_arguments = dict(arguments)
        if name not in {"patient_search", "get_location_details"}:
            mcp_arguments["session_id"] = session_id

        tool_functions = {
            "patient_search": patient_search,
            "validate_patient": validate_patient,
            "get_available_slots": get_available_slots,
            "book_appointment": book_appointment,
            "get_patient_appointments": get_patient_appointments,
            "cancel_patient_appointment": cancel_patient_appointment,
            "get_location_details": get_location_details,
            "handoff_to_human": handoff_to_human,
        }
        if name in {
            "validate_patient",
            "get_available_slots",
            "book_appointment",
            "get_patient_appointments",
            "cancel_patient_appointment",
        }:
            return tool_functions[name](
                **mcp_arguments,
                repository=self.clinic_repository,
                state_repository=self.session_state_repository,
            )
        return tool_functions[name](**mcp_arguments, repository=self.clinic_repository)


def seed_test_database(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        session.add_all(
            [
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
                ClinicLocation(
                    id="main-clinic",
                    name="Main Clinic",
                    address="100 Wellness Ave, Springfield",
                    hours="Mon-Fri 8:00 AM - 5:00 PM",
                ),
                ClinicLocation(
                    id="north-clinic",
                    name="North Clinic",
                    address="22 Care Street, Springfield",
                    hours="Mon-Fri 9:00 AM - 6:00 PM",
                ),
            ]
        )
        session.commit()
