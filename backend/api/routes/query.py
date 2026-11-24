from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
import asyncio
from models.request import QueryRequest
from models.response import QueryResponse
from core.pipeline import run_pipeline
from db.repositories.query_repo import save_query_result, get_user_history, get_all_stats
from core.auth.auth_handler import decode_token
from utils.logger import get_logger

router = APIRouter(prefix="/api", tags=["query"])
logger = get_logger(__name__)
QUERY_TIMEOUT_SECONDS = 75.0


def get_user_id_from_request(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = decode_token(token)
        return payload.get("sub")
    return None


@router.post("/query", response_model=QueryResponse)
async def handle_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
) -> QueryResponse:
    if not request.enabled_models:
        raise HTTPException(
            status_code=400,
            detail="At least one model must be enabled."
        )

    try:
        result = await asyncio.wait_for(run_pipeline(request), timeout=QUERY_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Query processing timed out. A model or evidence source was too slow; please retry.")
    user_id = get_user_id_from_request(http_request)
    background_tasks.add_task(save_query_result, request, result, user_id)

    return result


@router.get("/models")
async def list_models():
    from config.model_registry import MODEL_REGISTRY
    return {
        model_id: {
            "id": cfg.id,
            "display_name": cfg.display_name,
            "provider": cfg.provider,
            "enabled_by_default": cfg.enabled_by_default,
        }
        for model_id, cfg in MODEL_REGISTRY.items()
    }


@router.get("/history")
async def get_history(http_request: Request):
    user_id = get_user_id_from_request(http_request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    history = await get_user_history(user_id)
    return history


@router.get("/stats")
async def get_stats(http_request: Request):
    user_id = get_user_id_from_request(http_request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    stats = await get_all_stats(user_id)
    return stats