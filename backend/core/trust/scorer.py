from models.response import (
    ModelResponse, HallucinationResult, ComparisonResult, TrustScore,
    VerificationResult,
)


def compute_trust_scores(
    responses: list[ModelResponse],
    hallucination_results: list[HallucinationResult],
    comparison: ComparisonResult,
    rag_scores: dict[str, float] | None = None,
    verifications: dict[str, VerificationResult] | None = None,
) -> list[TrustScore]:
    scores = []
    for response in responses:
        verification = (verifications or {}).get(response.model_id, VerificationResult())
        consensus = comparison.consensus_scores.get(response.model_id, 0.0)
        similarity = comparison.similarity_scores.get(response.model_id, 0.0)
        verified = verification.score
        override = verification.contradicted > 0 or verified < 0.35
        score = 0.4 * consensus + 0.4 * verified + 0.2 * similarity
        if override:
            score = min(score, 0.49)
        if response.error:
            score = 0.0
        total = len(verification.claims)
        scores.append(TrustScore(
            model_id=response.model_id, score=max(0.0, min(1.0, score)),
            agreement_component=consensus, consensus_component=consensus,
            similarity_component=similarity, rag_component=verified,
            completeness_component=verification.supported / total if total else 0.0,
            supported_claims=verification.supported,
            contradicted_claims=verification.contradicted,
            unverified_claims=total - verification.supported - verification.contradicted,
            claims=verification.claims, factual_override=override,
        ))
    return scores