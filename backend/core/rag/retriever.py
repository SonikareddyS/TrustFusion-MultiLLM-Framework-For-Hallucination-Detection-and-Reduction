import numpy as np
import faiss
from core.rag.embedder import embed_texts, chunk_text
from utils.logger import get_logger
from models.response import EvidenceSource
from pydantic import BaseModel

logger = get_logger(__name__)


class EvidenceChunk(BaseModel):
    text: str
    source: EvidenceSource
    similarity: float


def retrieve_evidence(query: str, sources: list[EvidenceSource],
                      min_similarity: float = 0.45, top_k: int = 24,
                      claim_queries: list[str] | None = None) -> list[EvidenceChunk]:
    candidates = [(chunk, source) for source in sources
                  for chunk in chunk_text(source.text, chunk_size=100)]
    if not candidates:
        return []
    vectors = np.ascontiguousarray(embed_texts([text for text, _ in candidates]), dtype=np.float32)
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    query_vector = np.ascontiguousarray(embed_texts([query]), dtype=np.float32)
    faiss.normalize_L2(query_vector)
    distances, indices = index.search(query_vector, min(top_k, len(candidates)))
    selected = {int(idx) for score, idx in zip(distances[0], indices[0])
                if idx >= 0 and score >= min_similarity}
    relevance = vectors @ query_vector[0]
    if claim_queries:
        eligible = np.flatnonzero(relevance >= min_similarity)
        if len(eligible):
            claim_index = faiss.IndexFlatIP(vectors.shape[1])
            claim_index.add(vectors[eligible])
            claim_vectors = np.ascontiguousarray(embed_texts(claim_queries), dtype=np.float32)
            faiss.normalize_L2(claim_vectors)
            claim_scores, claim_indices = claim_index.search(claim_vectors, min(2, len(eligible)))
            for row_scores, row_indices in zip(claim_scores, claim_indices):
                selected.update(int(eligible[idx]) for score, idx in zip(row_scores, row_indices)
                                if idx >= 0 and score >= min_similarity)
    return [EvidenceChunk(text=candidates[idx][0], source=candidates[idx][1],
                          similarity=float(relevance[idx]))
            for idx in sorted(selected, key=lambda idx: -relevance[idx])]


def build_faiss_index(texts: list[str]) -> tuple[faiss.Index, list[str]]:
    all_chunks = []
    for text in texts:
        chunks = chunk_text(text)
        all_chunks.extend(chunks)

    if not all_chunks:
        return None, []

    embeddings = embed_texts(all_chunks)
    dimension = embeddings.shape[1]

    embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))

    logger.info("faiss_index_built", chunks=len(all_chunks))
    return index, all_chunks


def search_index(
    index: faiss.Index,
    chunks: list[str],
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.45,
) -> list[str]:
    if index is None or not chunks:
        return []

    query_embedding = embed_texts([query])
    query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)
    faiss.normalize_L2(query_embedding)
    distances, indices = index.search(
        query_embedding.astype(np.float32), top_k
    )

    results = []
    for score, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(chunks) and score >= min_similarity:
            results.append(chunks[idx])

    return results