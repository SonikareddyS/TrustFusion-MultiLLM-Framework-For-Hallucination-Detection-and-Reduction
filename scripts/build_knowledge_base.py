"""
Builds FAISS index from collected articles.
Run once after collect_articles.py
"""
import json
import pickle
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / "backend"))

import faiss
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("data/knowledge_base")
INDEX_PATH = DATA_DIR / "faiss_index.bin"
CHUNKS_PATH = DATA_DIR / "chunks.pkl"
CHUNK_SIZE = 150  # words per chunk
OVERLAP = 30      # overlap between chunks


def chunk_text(text: str, title: str, source: str) -> list[dict]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), CHUNK_SIZE - OVERLAP):
        chunk_words = words[i:i + CHUNK_SIZE]
        if len(chunk_words) < 20:
            continue
        chunks.append({
            "text": " ".join(chunk_words),
            "source": source,
            "title": title,
        })
    return chunks


def build_index():
    articles_file = DATA_DIR / "articles.json"
    if not articles_file.exists():
        print("❌ articles.json not found! Run collect_articles.py first.")
        return

    with open(articles_file, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"📚 Processing {len(articles)} articles...")

    all_chunks = []
    for article in articles:
        chunks = chunk_text(
            article["content"],
            article["title"],
            article["source"],
        )
        all_chunks.extend(chunks)

    print(f"📝 Created {len(all_chunks)} chunks")
    print("🔢 Generating embeddings (this takes 2-3 mins)...")

    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype(np.float32))

    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(all_chunks, f)

    print(f"\n✅ FAISS index built!")
    print(f"   Index: {INDEX_PATH}")
    print(f"   Chunks: {len(all_chunks)}")
    print(f"   Dimension: {dimension}")


if __name__ == "__main__":
    build_index()