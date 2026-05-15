from pydantic import BaseModel


class ConversationMessage(BaseModel):
    role: str
    content: str


class ConversationMemory:
    def __init__(self) -> None:
        self._messages_by_session: dict[str, list[ConversationMessage]] = {}
        self._state_by_session: dict[str, dict] = {}

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self._messages_by_session.setdefault(session_id, []).append(
            ConversationMessage(role=role, content=content)
        )

    def get_messages(self, session_id: str) -> list[ConversationMessage]:
        return list(self._messages_by_session.get(session_id, []))

    def get_state(self, session_id: str) -> dict:
        return dict(self._state_by_session.get(session_id, {}))

    def update_state(self, session_id: str, values: dict) -> None:
        self._state_by_session.setdefault(session_id, {}).update(values)

    def clear(self) -> None:
        self._messages_by_session.clear()
        self._state_by_session.clear()


memory_store = ConversationMemory()
