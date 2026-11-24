import asyncio
import time
from core.llm.base import BaseLLMClient, LLMOutput
from core.llm.groq_client import GroqClient
from core.llm.openrouter_client import OpenRouterClient
from config.model_registry import MODEL_REGISTRY
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_CLIENT_MAP: dict[str, BaseLLMClient] = {
    "gpt-oss-120b": GroqClient(
        model_id="gpt-oss-120b",
        display_name="GPT OSS 120B",
        groq_model="openai/gpt-oss-120b",
    ),
    "qwen-3.8-27b": GroqClient(
        model_id="qwen-3.8-27b",
        display_name="Qwen 3.8 27B",
        groq_model="qwen/qwen3.8-27b",
    ),
    "gemma-3-27b": GroqClient(
    model_id="gemma-3-27b",
    display_name="GPT OSS 20B",
    groq_model="openai/gpt-oss-20b",
),
    "mistral-large": OpenRouterClient(
        model_id="mistral-large",
        display_name="Mistral Large",
        openrouter_model="mistralai/mistral-large",
    ),
}


async def execute_parallel(
    prompt: str,
    enabled_model_ids: list[str],
    max_tokens: int = 1024,
) -> list[LLMOutput]:

    tasks: list[asyncio.Task] = []
    model_ids: list[str] = []

    async def generate_with_deadline(client):
        started = time.monotonic()
        try:
            return await asyncio.wait_for(client.generate(prompt, max_tokens), timeout=settings.llm_timeout)
        except asyncio.TimeoutError:
            return LLMOutput(model_id=client.model_id, text="",
                             latency_ms=(time.monotonic() - started) * 1000,
                             error=f"Model exceeded the {settings.llm_timeout}s response deadline.")

    for model_id in enabled_model_ids:
        if model_id not in MODEL_REGISTRY:
            logger.warning("unknown_model", model_id=model_id)
            continue
        client = _CLIENT_MAP.get(model_id)
        if client is None:
            logger.warning("model_not_implemented", model_id=model_id)
            continue
        tasks.append(asyncio.create_task(
            generate_with_deadline(client)
        ))
        model_ids.append(model_id)

    if not tasks:
        return []

    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    outputs: list[LLMOutput] = []
    for model_id, result in zip(model_ids, raw_results):
        if isinstance(result, Exception):
            outputs.append(LLMOutput(
                model_id=model_id,
                text="",
                latency_ms=0,
                error=str(result),
            ))
        else:
            outputs.append(result)

    return outputs