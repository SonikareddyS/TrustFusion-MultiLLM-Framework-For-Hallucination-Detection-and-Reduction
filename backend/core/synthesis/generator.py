import numpy as np

from core.rag.embedder import embed_texts
from models.response import FinalAnswer, VerificationResult


def synthesize_verified_answer(verifications: dict[str, VerificationResult],
                               total_enabled: int) -> FinalAnswer:
    candidates = [(model_id, claim) for model_id, result in verifications.items()
                  for claim in result.claims if claim.status == "SUPPORTED" and claim.source_url]
    if not candidates or total_enabled < 2:
        return FinalAnswer(text="Insufficient independently verified, cross-model evidence to answer safely.",
                           source_model_id="verified-synthesis", corrections_applied=[])
    vectors = embed_texts([claim.claim for _, claim in candidates])
    selected, selected_vectors = [], []
    for candidate_idx, (model_id, claim) in enumerate(candidates):
        supporters = {other_id for other_idx, (other_id, _) in enumerate(candidates)
                      if float(vectors[candidate_idx] @ vectors[other_idx]) >= 0.78}
        if len(supporters) <= total_enabled / 2:
            continue
        if any(float(vectors[candidate_idx] @ vector) >= 0.88 for vector in selected_vectors):
            continue
        selected.append(claim)
        selected_vectors.append(vectors[candidate_idx])
    text = "\n\n".join(f"- {claim.claim} [Source]({claim.source_url})" for claim in selected)
    return FinalAnswer(
        text=text or "No claims met both source-verification and majority-support requirements.",
        source_model_id="verified-synthesis",
        corrections_applied=[claim.claim for result in verifications.values()
                             for claim in result.claims if claim.status == "CONTRADICTED"],
    )