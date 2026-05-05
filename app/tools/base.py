import json
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str = ""

    @abstractmethod
    async def run(self, query: str = "", **kwargs: Any) -> str:
        raise NotImplementedError

    @staticmethod
    def clean_json(text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            return text
