import numpy as np
from functools import lru_cache
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
    try:
        return SentenceTransformer(settings.embedding_model, local_files_only=True)
    except OSError:
        return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> np.ndarray:
    return get_model().encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def chunk_text(text: str, chunk_size: int = 200) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks