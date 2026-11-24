from pydantic import BaseModel, Field
from typing import Optional
from config.model_registry import MODEL_REGISTRY


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    enabled_models: list[str] = Field(
        default_factory=lambda: [model.id for model in MODEL_REGISTRY.values() if model.enabled_by_default],
        description="Model IDs to query",
    )
    use_rag: bool = Field(default=True)
    session_id: Optional[str] = None
