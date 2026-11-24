import numpy as np
from core.comparison.similarity import compute_individual_agreement
from models.response import ModelResponse, HallucinationResult, HallucinationLabel
from utils.logger import get_logger

logger = get_logger(__name__)


def classify_responses(
    responses: list[ModelResponse],
    embeddings: np.ndarray,
    agreement_score: float,
    vagueness_flags: list[str],
    missing_info_flags: list[str],
    rag_scores: dict[str, float] = None,
) -> list[HallucinationResult]:

    results = []

    for idx, response in enumerate(responses):
        reasons = []
        score = 1.0

        # Individual agreement with other models
        if embeddings is not None and len(embeddings) > 1:
            individual_agreement = compute_individual_agreement(
                idx,
                [r.normalized_text for r in responses],
                embeddings,
            )
        else:
            individual_agreement = agreement_score

        # Agreement penalty
        if individual_agreement < 0.3:
            score -= 0.5
            reasons.append(
                f"Very low agreement with other models "
                f"({round(individual_agreement * 100)}%)"
            )
        elif individual_agreement < 0.5:
            score -= 0.3
            reasons.append(
                f"Low agreement with other models "
                f"({round(individual_agreement * 100)}%)"
            )
        elif individual_agreement < 0.7:
            score -= 0.1
            reasons.append(
                f"Moderate agreement ({round(individual_agreement * 100)}%)"
            )

        # RAG validation penalty/boost
        if rag_scores and response.model_id in rag_scores:
            rag_score = rag_scores[response.model_id]
            if rag_score < 0.3:
                score -= 0.4
                reasons.append(
                    f"RAG validation failed — response contradicts "
                    f"trusted sources (score: {round(rag_score * 100)}%)"
                )
            elif rag_score < 0.5:
                score -= 0.2
                reasons.append(
                    f"Weak RAG validation "
                    f"(score: {round(rag_score * 100)}%)"
                )
            elif rag_score > 0.7:
                score += 0.1
                reasons.append(
                    f"RAG validated — response aligns with "
                    f"trusted sources ({round(rag_score * 100)}%)"
                )

        # Vagueness penalty
        if response.model_id in vagueness_flags:
            score -= 0.15
            reasons.append("Response contains vague or uncertain language")

        # Missing info penalty
        if response.model_id in missing_info_flags:
            score -= 0.15
            reasons.append("Response may be missing key information")

        # Length penalty
        word_count = len(response.normalized_text.split())
        if word_count < 5:
            score -= 0.4
            reasons.append("Response is too short to be reliable")
        elif word_count < 15:
            score -= 0.2
            reasons.append("Response is very brief")

        # Error penalty
        if response.error:
            score = 0.0
            reasons.append("Model returned an error")

        score = max(0.0, min(1.0, score))

        # Classification
        if score >= 0.7:
            label = HallucinationLabel.reliable
        elif score >= 0.4:
            label = HallucinationLabel.suspicious
        else:
            label = HallucinationLabel.hallucinated

        if not reasons:
            reasons.append(
                f"Response aligns well with other models "
                f"({round(individual_agreement * 100)}% agreement)"
            )

        results.append(HallucinationResult(
            model_id=response.model_id,
            label=label,
            confidence=round(score, 3),
            reasons=reasons,
        ))

    return results