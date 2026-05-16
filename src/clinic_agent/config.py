import os


DEFAULT_DATABASE_URL = "postgresql+psycopg://clinic_agent:clinic_agent@localhost:5433/clinic_agent"
DEFAULT_MCP_SERVER_URL = "http://127.0.0.1:9100/mcp"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_mcp_server_url() -> str:
    return os.getenv("MCP_SERVER_URL", DEFAULT_MCP_SERVER_URL)
