from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMOutput:
    model_id: str
    text: str
    latency_ms: float
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class BaseLLMClient(ABC):

    def __init__(self, model_id: str, display_name: str):
        self.model_id = model_id
        self.display_name = display_name

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1024) -> LLMOutput:
        ...
