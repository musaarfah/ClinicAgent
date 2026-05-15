from clinic_agent.memory.store import ConversationMemory


def test_memory_stores_messages_by_session() -> None:
    memory = ConversationMemory()

    memory.add_message("session-1", "user", "hello")

    assert [message.content for message in memory.get_messages("session-1")] == ["hello"]
    assert memory.get_messages("missing") == []

