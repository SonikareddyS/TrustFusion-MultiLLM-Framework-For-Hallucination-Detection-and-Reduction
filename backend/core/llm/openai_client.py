import time
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm.base import BaseLLMClient, LLMOutput
from config.settings import settings


class OpenAIClient(BaseLLMClient):

    def __init__(self):
        super().__init__(model_id="gpt-4o", display_name="GPT-4o")
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def generate(self, prompt: str, max_tokens: int = 1024) -> LLMOutput:
        t0 = time.monotonic()
        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=settings.llm_timeout,
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