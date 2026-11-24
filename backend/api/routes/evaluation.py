from fastapi import APIRouter, Request
from core.auth.auth_handler import decode_token
from db.mongo import get_db
import datetime

router = APIRouter(prefix="/api/eval", tags=["evaluation"])


def get_user_id(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = decode_token(token)
        return payload.get("sub")
    return None


@router.get("/metrics")
async def get_metrics(request: Request):
    db = get_db()
    user_id = get_user_id(request)

    match_filter = {"user_id": user_id} if user_id else {}

    # Total queries
    total = await db.query_logs.count_documents(match_filter)

    if total == 0:
        return {
            "total_queries": 0,
            "rag_trigger_rate": 0,
            "hallucination_rate": 0,
            "avg_agreement": 0,
            "avg_latency_ms": 0,
            "model_performance": [],
            "recent_trend": [],
        }

    # RAG trigger rate
    rag_count = await db.query_logs.count_documents(
        {**match_filter, "rag_triggered": True}
    )

    # Hallucination rate
    hallucination_count = await db.query_logs.count_documents(
        {**match_filter, "hallucination_count": {"$gt": 0}}
    )

    # Average agreement and latency
    pipeline = [
        {"$match": match_filter},
        {"$group": {
            "_id": None,
            "avg_agreement": {"$avg": "$agreement_score"},
            "avg_latency": {"$avg": "$total_latency_ms"},
        }}
    ]
    agg_result = await db.query_logs.aggregate(pipeline).to_list(1)
    avg_agreement = agg_result[0]["avg_agreement"] if agg_result else 0
    avg_latency = agg_result[0]["avg_latency"] if agg_result else 0

    # Model performance
    model_pipeline = [
        {"$match": match_filter},
        {"$unwind": "$trust_scores"},
        {"$group": {
            "_id": "$trust_scores.model_id",
            "avg_trust": {"$avg": "$trust_scores.score"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"avg_trust": -1}}
    ]
    model_perf = await db.query_logs.aggregate(model_pipeline).to_list(20)

    # Recent trend (last 10 queries)
    trend_cursor = db.query_logs.find(
        match_filter,
        {"agreement_score": 1, "hallucination_count": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10)
    trend = []
    async for doc in trend_cursor:
        trend.append({
            "agreement": round(doc["agreement_score"] * 100),
            "hallucinations": doc["hallucination_count"],
            "date": doc["created_at"].strftime("%d %b"),
        })
    trend.reverse()

    return {
        "total_queries": total,
        "rag_trigger_rate": round(rag_count / total * 100, 1),
        "hallucination_rate": round(hallucination_count / total * 100, 1),
        "avg_agreement": round(avg_agreement * 100, 1),
        "avg_latency_ms": round(avg_latency, 0),
        "model_performance": [
            {
                "model_id": m["_id"],
                "avg_trust": round(m["avg_trust"] * 100, 1),
                "query_count": m["count"],
            }
            for m in model_perf
        ],
        "recent_trend": trend,
    }