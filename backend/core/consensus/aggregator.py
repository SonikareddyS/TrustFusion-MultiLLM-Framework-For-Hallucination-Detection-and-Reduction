"""
Aggregates consensus voting results with trust scores
to produce final hallucination labels.
"""
from models.response import (
    ModelResponse, HallucinationResult, HallucinationLabel,
    TrustScore,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def apply_consensus_to_hallucination(
    hallucination_results: list[HallucinationResult],
    consensus_result: dict,
    trust_scores: list[TrustScore],
) -> list[HallucinationResult]:
    """
    Updates hallucination labels based on consensus voting.
    Minority voters get penalized trust scores.
    """
    winner_models = set(consensus_result.get("winner_models", []))
    minority_models = set(consensus_result.get("minority_models", []))
    confidence = consensus_result.get("consensus_confidence", 0.5)

    updated = []
    for result in hallucination_results:
        model_id = result.model_id
        reasons = list(result.reasons)
        label = result.label
        new_confidence = result.confidence

        if model_id in minority_models:
            # Penalize minority voters
            new_confidence = max(0.0, result.confidence - 0.3)
            reasons.append(
                f"Consensus voting: this model is in minority "
                f"({len(minority_models)} vs "
                f"{consensus_result.get('majority_size', 0)} majority models)"
            )
            if new_confidence < 0.4:
                label = HallucinationLabel.suspicious
            if new_confidence < 0.2:
                label = HallucinationLabel.hallucinated

        elif model_id in winner_models:
            # Boost majority voters
            new_confidence = min(1.0, result.confidence + 0.1)
            if confidence >= 0.6 and label == HallucinationLabel.suspicious:
                label = HallucinationLabel.reliable
                reasons.append("Consensus voting: agrees with majority")

        updated.append(HallucinationResult(
            model_id=model_id,
            label=label,
            confidence=round(new_confidence, 3),
            reasons=reasons,
        ))

    return updated


def get_consensus_final_answer(
    responses: list[ModelResponse],
    consensus_result: dict,
    trust_scores: list[TrustScore],
) -> tuple[str, str]:
    """
    Select best answer from majority cluster.
    Returns (best_text, best_model_id)
    """
    winner_models = set(consensus_result.get("winner_models", []))

    # Filter to majority models only
    majority_responses = [
        r for r in responses
        if r.model_id in winner_models and not r.error
    ]

    if not majority_responses:
        # Fallback to highest trust score
        best_trust = max(trust_scores, key=lambda t: t.score, default=None)
        if best_trust:
            matched = next(
                (r for r in responses if r.model_id == best_trust.model_id),
                None,
            )
            if matched:
                return matched.normalized_text, matched.model_id
        return "No valid response obtained.", "none"

    # Among majority, pick highest trust score
    majority_trust = [
        t for t in trust_scores
        if t.model_id in winner_models
    ]

    if majority_trust:
        best = max(majority_trust, key=lambda t: t.score)
        matched = next(
            (r for r in majority_responses if r.model_id == best.model_id),
            None,
        )
        if matched:
            return matched.normalized_text, matched.model_id

    # Fallback to first majority response
    return majority_responses[0].normalized_text, majority_responses[0].model_id