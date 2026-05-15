from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from clinic_agent.config import get_database_url

_session_factory: sessionmaker[Session] | None = None
_session_factory_url: str | None = None


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    engine = create_engine(database_url or get_database_url())
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory, _session_factory_url

    database_url = get_database_url()
    if _session_factory is None or _session_factory_url != database_url:
        _session_factory = create_session_factory(database_url)
        _session_factory_url = database_url
    return _session_factory


def reset_session_factory() -> None:
    global _session_factory, _session_factory_url

    _session_factory = None
    _session_factory_url = None


@contextmanager
def session_scope(session_factory: sessionmaker[Session] | None = None) -> Iterator[Session]:
    session = (session_factory or get_session_factory())()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
