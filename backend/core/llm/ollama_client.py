import time
import httpx
from core.llm.base import BaseLLMClient, LLMOutput


class OllamaClient(BaseLLMClient):

    def __init__(self, model_id: str, display_name: str, ollama_model: str):
        super().__init__(model_id=model_id, display_name=display_name)
        self._ollama_model = ollama_model
        self._base_url = "http://localhost:11434/api/generate"

    async def generate(self, prompt: str, max_tokens: int = 1024) -> LLMOutput:
        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    self._base_url,
                    json={
                        "model": self._ollama_model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "")
                return LLMOutput(
                    model_id=self.model_id,
                    text=text,
                    latency_ms=(time.monotonic() - t0) * 1000,
                )
        except Exception as exc:
            return LLMOutput(
                model_id=self.model_id,
                text="",
                latency_ms=(time.monotonic() - t0) * 1000,
                error=str(exc),
            )