import time
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm.base import BaseLLMClient, LLMOutput
from config.settings import settings


class ClaudeClient(BaseLLMClient):

    def __init__(self):
        super().__init__(model_id="claude-3-5-sonnet", display_name="Claude 3.5 Sonnet")
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def generate(self, prompt: str, max_tokens: int = 1024) -> LLMOutput:
        t0 = time.monotonic()
        try:
            response = await self._client.messages.create(
                model=settings.claude_model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text if response.content else ""
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
