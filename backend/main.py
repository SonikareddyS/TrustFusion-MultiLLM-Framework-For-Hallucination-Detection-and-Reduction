from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import ConnectionFailure

from api.routes.query import router as query_router
from api.routes.auth import router as auth_router
from api.routes.evaluation import router as eval_router
from db.mongo import connect_mongo, close_mongo
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup: connecting to MongoDB")
    await connect_mongo()
    yield
    logger.info("shutdown: closing MongoDB connection")
    await close_mongo()


app = FastAPI(
    title="Trust-Aware Multi-LLM System",
    version="1.0.0",
    description="Hallucination detection via multi-LLM consensus.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router)
app.include_router(auth_router)
app.include_router(eval_router)


@app.exception_handler(ConnectionFailure)
async def database_unavailable_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database unavailable. Start MongoDB and try again."},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)