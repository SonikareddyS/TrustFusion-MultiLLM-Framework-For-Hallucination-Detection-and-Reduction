import time
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm.base import BaseLLMClient, LLMOutput
from config.settings import settings


class GeminiClient(BaseLLMClient):

    def __init__(self):
        super().__init__(model_id="gemini-1.5-pro", display_name="Gemini 1.5 Pro")
        genai.configure(api_key=settings.google_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def generate(self, prompt: str, max_tokens: int = 1024) -> LLMOutput:
        t0 = time.monotonic()
        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                ),
            )
            text = response.text or ""
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
