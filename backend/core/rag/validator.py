import re
from functools import lru_cache

import numpy as np

from core.rag.embedder import embed_texts
from core.rag.retriever import EvidenceChunk
from models.response import ClaimVerification, ModelResponse, VerificationResult


def extract_claims(text: str) -> list[str]:
    text = text.replace("\u202f", " ").replace("\u00a0", " ")
    text = re.sub(r"\u3010[^\u3011]*\u3011", "", text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://[^\s<>]+", "", text)
    claims = []
    lines = text.splitlines()
    for line_idx, line in enumerate(lines):
        if re.match(r"^\s*#{1,6}\s", line) or re.fullmatch(r"\s*\*\*[^*]+\*\*\s*", line):
            continue
        if "|" in line and line_idx + 1 < len(lines) and re.fullmatch(r"[| :\-]+", lines[line_idx + 1]):
            continue
        line = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", line)
        line = line.replace("**", "").strip()
        if not line or re.fullmatch(r"[| :\-]+", line):
            continue
        if "|" in line:
            cells = [cell.strip() for cell in line.strip("|").split("|") if cell.strip()]
            line = ": ".join(cells)
        for sentence in re.split(r"(?<!\b[A-Z]\.)(?<=[.!?])\s+|;\s*|\s+and\s+(?=(?:it|they|he|she|AI|[A-Z][a-z]+)\s+(?:is|are|was|were|uses|can)\b)", line):
            if len(sentence.split()) >= 4 and not sentence.endswith((":", "?")):
                claims.append(sentence.strip())
    return list(dict.fromkeys(claims))


@lru_cache(maxsize=1)
def get_nli_model():
    from sentence_transformers import CrossEncoder
    try:
        return CrossEncoder("cross-encoder/nli-deberta-v3-small", max_length=512,
                            local_files_only=True)
    except OSError:
        return CrossEncoder("cross-encoder/nli-deberta-v3-small", max_length=512)


def predict_nli(pairs: list[tuple[str, str]]) -> list[dict[str, float]]:
    model = get_nli_model()
    labels = {int(index): label.lower() for index, label in model.model.config.id2label.items()}
    if set(labels.values()) != {"contradiction", "entailment", "neutral"}:
        raise RuntimeError(f"Unsupported NLI label mapping: {labels}")
    predictions = model.predict(pairs, apply_softmax=True, show_progress_bar=False)
    return [{labels[index]: float(value) for index, value in enumerate(row)}
            for row in predictions]


def verify_responses(responses: list[ModelResponse], chunks: list[EvidenceChunk],
                     query: str) -> dict[str, VerificationResult]:
    evidence = list(dict.fromkeys(
        (sentence, chunk.source.url) for chunk in chunks
        for sentence in re.split(r"(?<!\b[A-Z]\.)(?<=[.!?])\s+", chunk.text)
        if len(sentence.split()) >= 4))
    vectors = embed_texts([text for text, _ in evidence]) if evidence else None
    query_vector = embed_texts([query])[0] if evidence else None
    prediction_cache = {}
    results = {}
    for response in responses:
        claims = extract_claims(response.raw_text)
        checked = [ClaimVerification(claim=claim, status="UNVERIFIED") for claim in claims]
        if evidence and claims and not response.error:
            claim_vectors = embed_texts(claims)
            pairs, locations = [], []
            for claim_idx, vector in enumerate(claim_vectors):
                if float(vector @ query_vector) < 0.20:
                    continue
                similarities = vectors @ vector
                seen_sources = set()
                for evidence_idx in np.argsort(similarities)[::-1]:
                    source_url = evidence[evidence_idx][1]
                    if source_url in seen_sources:
                        continue
                    seen_sources.add(source_url)
                    if similarities[evidence_idx] >= 0.55:
                        pairs.append((evidence[evidence_idx][0], claims[claim_idx]))
                        locations.append((claim_idx, evidence_idx, float(similarities[evidence_idx])))
            pending_pairs = list(dict.fromkeys(pair for pair in pairs if pair not in prediction_cache))
            if pending_pairs:
                prediction_cache.update(zip(pending_pairs, predict_nli(pending_pairs)))
            predictions = [prediction_cache[pair] for pair in pairs]
            for (claim_idx, evidence_idx, similarity), prediction in zip(locations, predictions):
                premise, url = evidence[evidence_idx]
                contradiction = prediction["contradiction"] >= 0.85 and similarity >= 0.72
                numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", claims[claim_idx]))
                supported = (prediction["entailment"] >= 0.85
                             and numbers.issubset(set(re.findall(r"\b\d+(?:\.\d+)?\b", premise))))
                previous = checked[claim_idx]
                if contradiction or (supported and previous.status != "CONTRADICTED"
                                     and prediction["entailment"] > previous.confidence):
                    checked[claim_idx] = ClaimVerification(
                        claim=claims[claim_idx], status="CONTRADICTED" if contradiction else "SUPPORTED",
                        evidence=premise, source_url=url,
                        confidence=prediction["contradiction" if contradiction else "entailment"],
                    )
        supported_count = sum(claim.status == "SUPPORTED" for claim in checked)
        contradicted_count = sum(claim.status == "CONTRADICTED" for claim in checked)
        score = max(0.0, min(1.0, (supported_count - 0.5 * contradicted_count) / len(checked))) if checked else 0.0
        results[response.model_id] = VerificationResult(score=score, claims=checked)
    return results