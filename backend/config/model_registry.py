from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    id: str
    display_name: str
    provider: str
    enabled_by_default: bool = True
    max_tokens: int = 1024
    description: Optional[str] = None


MODEL_REGISTRY: dict[str, ModelConfig] = {
    "gpt-oss-120b": ModelConfig(
        id="gpt-oss-120b",
        display_name="GPT OSS 120B",
        provider="groq",
        description="OpenAI's 120B open-weight model via Groq",
    ),
    "qwen-3.8-27b": ModelConfig(
        id="qwen-3.8-27b",
        display_name="Qwen 3.8 27B",
        provider="groq",
        description="Qwen's 27B model via Groq",
    ),
    "gemma-3-27b": ModelConfig(
    id="gemma-3-27b",
    display_name="GPT OSS 20B",
    provider="groq",
    description="OpenAI's open source model via Groq",
),
    "mistral-large": ModelConfig(
        id="mistral-large",
        display_name="Mistral Large",
        provider="openrouter",
        enabled_by_default=False,
        description="Requires OpenRouter credits",
    ),
}