import os


DEFAULT_DATABASE_URL = "postgresql+psycopg://clinic_agent:clinic_agent@localhost:5433/clinic_agent"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

