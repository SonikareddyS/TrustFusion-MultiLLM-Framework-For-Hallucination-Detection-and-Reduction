import pickle
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from utils.logger import get_logger

logger = get_logger(__name__)

# Fix path resolution
_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = _BASE_DIR / "data" / "knowledge_base"
INDEX_PATH = DATA_DIR / "faiss_index.bin"
CHUNKS_PATH = DATA_DIR / "chunks.pkl"

_index = None
_chunks = None
_model = SentenceTransformer("all-MiniLM-L6-v2")


def load_index():
    global _index, _chunks
    if _index is not None:
        return True

    if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
        logger.warning("local_index_not_found", path=str(INDEX_PATH))
        return False

    try:
        _index = faiss.read_index(str(INDEX_PATH))
        with open(CHUNKS_PATH, "rb") as f:
            _chunks = pickle.load(f)
        logger.info("local_index_loaded", chunks=len(_chunks))
        return True
    except Exception as e:
        logger.error("index_load_failed", error=str(e))
        return False


def search_local(query: str, top_k: int = 5) -> tuple[list[str], list[str]]:
    if not load_index():
        return [], []

    query_embedding = _model.encode([query])
    distances, indices = _index.search(
        query_embedding.astype(np.float32), top_k
    )

    results = []
    sources = []
    seen_sources = set()

    for rank, idx in enumerate(indices[0]):
        if 0 <= idx < len(_chunks):
            chunk = _chunks[idx]
            # Only include chunks with low distance (relevant)
            if distances[0][rank] < 100:
                results.append(chunk["text"])
                source = chunk["source"]
                if source not in seen_sources:
                    sources.append(source)
                    seen_sources.add(source)

    logger.info(
        "local_search_complete",
        results=len(results),
        sources=sources,
    )
    return results, sources