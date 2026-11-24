import datetime
from models.request import QueryRequest
from models.response import QueryResponse
from db.mongo import get_db


async def save_query_result(
    request: QueryRequest,
    result: QueryResponse,
    user_id: str = None,
) -> None:
    db = get_db()
    doc = {
        "query": request.query,
        "session_id": request.session_id,
        "enabled_models": request.enabled_models,
        "user_id": user_id,
        "agreement_score": result.comparison.agreement_score,
        "total_latency_ms": result.total_latency_ms,
        "rag_triggered": len(result.explanation.rag_sources_used) > 0,
        "hallucination_count": sum(
            1 for h in result.hallucination_results
            if h.label.value != "reliable"
        ),
        "final_answer": result.final_answer.text[:500],
        "source_model": result.final_answer.source_model_id,
        "trust_scores": [
            {"model_id": t.model_id, "score": t.score}
            for t in result.trust_scores
        ],
        "created_at": datetime.datetime.utcnow(),
    }
    await db.query_logs.insert_one(doc)


async def get_user_history(user_id: str, limit: int = 20) -> list:
    db = get_db()
    cursor = db.query_logs.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit)

    history = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["created_at"] = doc["created_at"].isoformat()
        history.append(doc)
    return history


async def get_all_stats(user_id: str) -> dict:
    db = get_db()
    total = await db.query_logs.count_documents({"user_id": user_id})
    rag_count = await db.query_logs.count_documents(
        {"user_id": user_id, "rag_triggered": True}
    )
    hallucination_count = await db.query_logs.count_documents(
        {"user_id": user_id, "hallucination_count": {"$gt": 0}}
    )
    return {
        "total_queries": total,
        "rag_triggered_count": rag_count,
        "hallucination_detected_count": hallucination_count,
    }