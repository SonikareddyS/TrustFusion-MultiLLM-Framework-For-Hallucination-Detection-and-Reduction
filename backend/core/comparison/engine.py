import numpy as np
from core.comparison.similarity import compute_pairwise_similarity, compute_individual_agreement
from core.comparison.contradiction import detect_contradictions, detect_vagueness, detect_missing_info
from models.response import ModelResponse, ComparisonResult
from utils.logger import get_logger

logger = get_logger(__name__)


def run_comparison(
    responses: list[ModelResponse],
    query: str,
    total_enabled: int | None = None,
) -> tuple[ComparisonResult, np.ndarray]:

    if not responses:
        return ComparisonResult(
            contradictions=[],
            agreement_score=0.0,
            missing_info_flags=[],
            vagueness_flags=[],
        ), np.array([])

    texts = [r.normalized_text for r in responses]

    similarity_result = compute_pairwise_similarity(texts)
    agreement_score = similarity_result["average"]
    embeddings = similarity_result.get("embeddings", np.array([]))
    pairs = similarity_result.get("pairs", [])
    denominator = max(total_enabled or len(responses), len(responses))
    matrix = np.eye(len(responses))
    for left, right, score in pairs:
        matrix[left, right] = matrix[right, left] = score
    clusters = []
    for response_idx in range(len(responses)):
        cluster = next((members for members in clusters
                        if all(matrix[response_idx, member] >= 0.78 for member in members)), None)
        if cluster is None:
            clusters.append([response_idx])
        else:
            cluster.append(response_idx)
    consensus_scores = {responses[member].model_id: len(cluster) / denominator
                        for cluster in clusters for member in cluster}
    similarity_scores = {
        response.model_id: max(0.0, float((matrix[idx].sum() - 1) / (len(responses) - 1)))
        if len(responses) > 1 else 0.0
        for idx, response in enumerate(responses)
    }
    agreement_score = sum(consensus_scores.values()) / denominator

    response_dict = {
        r.model_id: r.normalized_text
        for r in responses
    }

    # Pass similarity pairs to avoid false contradictions
    contradictions = detect_contradictions(response_dict, pairs)

    vagueness_flags = [
        r.model_id
        for r in responses
        if detect_vagueness(r.normalized_text)
    ]

    missing_info_flags = [
        r.model_id
        for r in responses
        if detect_missing_info(r.normalized_text, query)
    ]

    logger.info(
        "comparison_complete",
        agreement=round(agreement_score, 3),
        contradictions=len(contradictions),
    )

    return ComparisonResult(
        contradictions=contradictions,
        agreement_score=agreement_score,
        missing_info_flags=missing_info_flags,
        vagueness_flags=vagueness_flags,
        consensus_scores=consensus_scores,
        similarity_scores=similarity_scores,
    ), embeddings