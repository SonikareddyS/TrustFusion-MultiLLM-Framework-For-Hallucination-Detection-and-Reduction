import numpy as np
from core.rag.embedder import embed_texts
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_embeddings(texts: list[str]) -> np.ndarray:
    return embed_texts(texts)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compute_pairwise_similarity(texts: list[str]) -> dict:
    if len(texts) < 2:
        return {"average": 0.0, "matrix": [], "pairs": [],
            "embeddings": compute_embeddings(texts) if texts else np.array([])}

    embeddings = compute_embeddings(texts)
    pairs = []
    scores = []

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            score = cosine_similarity(embeddings[i], embeddings[j])
            pairs.append((i, j, score))
            scores.append(score)

    return {
        "average": float(np.mean(scores)),
        "matrix": embeddings.tolist(),
        "pairs": pairs,
        "embeddings": embeddings,
    }


def compute_individual_agreement(
    target_idx: int,
    all_texts: list[str],
    embeddings: np.ndarray,
) -> float:
    scores = []
    for i, _ in enumerate(all_texts):
        if i != target_idx:
            score = cosine_similarity(embeddings[target_idx], embeddings[i])
            scores.append(score)
    return float(np.mean(scores)) if scores else 1.0