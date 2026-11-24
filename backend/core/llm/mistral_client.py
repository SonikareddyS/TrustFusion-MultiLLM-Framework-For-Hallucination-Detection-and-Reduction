import time
from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import ChatMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm.base import BaseLLMClient, LLMOutput
from config.settings import settings


class MistralClient(BaseLLMClient):

    def __init__(self):
        super().__init__(model_id="mistral-large", display_name="Mistral Large")
        self._client = MistralAsyncClient(api_key=settings.mistral_api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def generate(self, prompt: str, max_tokens: int = 1024) -> LLMOutput:
        t0 = time.monotonic()
        try:
            response = await self._client.chat(
                model=settings.mistral_model,
                messages=[ChatMessage(role="user", content=prompt)],
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content or ""
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
