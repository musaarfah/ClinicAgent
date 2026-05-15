from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    description: str
    parameters: dict = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    @abstractmethod
    def run(self, arguments: dict) -> dict:
        raise NotImplementedError

    def openai_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
