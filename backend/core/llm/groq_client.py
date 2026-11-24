import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm.base import BaseLLMClient, LLMOutput
from config.settings import settings


class GroqClient(BaseLLMClient):

    def __init__(self, model_id: str, display_name: str, groq_model: str):
        super().__init__(model_id=model_id, display_name=display_name)
        self._groq_model = groq_model
        self._base_url = "https://api.groq.com/openai/v1/chat/completions"
        self._headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def generate(self, prompt: str, max_tokens: int = 1024) -> LLMOutput:
        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    self._base_url,
                    headers=self._headers,
                    json={
                        "model": self._groq_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"] or ""
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