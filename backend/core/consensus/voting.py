"""
Consensus voting algorithm.
Models vote on answers and majority wins.
Minority voters are flagged as potential hallucinations.
"""
import re
from collections import Counter
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_key_claims(text: str) -> list[str]:
    """Extract key factual claims from response."""
    text = text.lower().strip()
    sentences = re.split(r'[.!?]+', text)
    claims = []
    for s in sentences:
        s = s.strip()
        if len(s.split()) >= 5:
            claims.append(s)
    return claims[:5]  # top 5 claims


def compute_semantic_clusters(
    responses: dict[str, str],
    similarity_threshold: float = 0.6,
) -> list[list[str]]:
    """
    Group models into clusters based on response similarity.
    Models in same cluster agree with each other.
    """
    from sentence_transformers import SentenceTransformer
    import numpy as np

    model_ids = list(responses.keys())
    texts = list(responses.values())

    if len(texts) < 2:
        return [model_ids]

    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = encoder.encode(texts, convert_to_numpy=True)

    # Compute similarity matrix
    similarity_matrix = np.zeros((len(texts), len(texts)))
    for i in range(len(texts)):
        for j in range(len(texts)):
            if i != j:
                dot = np.dot(embeddings[i], embeddings[j])
                norm = np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                similarity_matrix[i][j] = dot / norm if norm > 0 else 0

    # Cluster models
    visited = set()
    clusters = []

    for i in range(len(model_ids)):
        if i in visited:
            continue
        cluster = [model_ids[i]]
        visited.add(i)
        for j in range(len(model_ids)):
            if j not in visited and similarity_matrix[i][j] >= similarity_threshold:
                cluster.append(model_ids[j])
                visited.add(j)
        clusters.append(cluster)

    logger.info("consensus_clusters", clusters=clusters)
    return clusters


def run_consensus_vote(
    responses: dict[str, str],
) -> dict:
    """
    Run majority voting across model responses.
    Returns winner cluster, minority models, and confidence.
    """
    if not responses:
        return {
            "winner_models": [],
            "minority_models": [],
            "consensus_confidence": 0.0,
            "clusters": [],
            "majority_size": 0,
            "total_models": 0,
        }

    # Filter out empty responses
    valid_responses = {
        k: v for k, v in responses.items()
        if v and len(v.split()) > 5
    }

    if not valid_responses:
        return {
            "winner_models": list(responses.keys()),
            "minority_models": [],
            "consensus_confidence": 0.0,
            "clusters": [],
            "majority_size": 0,
            "total_models": len(responses),
        }

    # Cluster models by similarity
    clusters = compute_semantic_clusters(valid_responses)

    # Find majority cluster
    clusters_sorted = sorted(clusters, key=len, reverse=True)
    majority_cluster = clusters_sorted[0]

    # All other clusters are minority
    minority_models = []
    for cluster in clusters_sorted[1:]:
        minority_models.extend(cluster)

    # Consensus confidence
    total = len(valid_responses)
    majority_size = len(majority_cluster)
    confidence = majority_size / total if total > 0 else 0.0

    logger.info(
        "consensus_vote_complete",
        majority=majority_cluster,
        minority=minority_models,
        confidence=round(confidence, 3),
    )

    return {
        "winner_models": majority_cluster,
        "minority_models": minority_models,
        "consensus_confidence": round(confidence, 3),
        "clusters": clusters,
        "majority_size": majority_size,
        "total_models": total,
    }