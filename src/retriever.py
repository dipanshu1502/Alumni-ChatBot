import pickle
import os
from functools import lru_cache
from pathlib import Path

import faiss

from embeddings import load_embedding_model

DEFAULT_MIN_SIMILARITY = 0.35


def get_min_similarity():
    try:
        value = float(os.getenv("PDF_MIN_SIMILARITY", str(DEFAULT_MIN_SIMILARITY)))
    except ValueError as exc:
        raise RuntimeError("PDF_MIN_SIMILARITY must be a number between -1 and 1.") from exc
    if not -1 <= value <= 1:
        raise RuntimeError("PDF_MIN_SIMILARITY must be between -1 and 1.")
    return value


@lru_cache(maxsize=1)
def load_vector_store():
    storage_folder = Path(__file__).resolve().parent.parent / "vector_db"
    index_path = storage_folder / "index.faiss"
    chunks_path = storage_folder / "chunks.pkl"

    if not index_path.exists() or not chunks_path.exists():
        raise RuntimeError("PDF vector store is missing. Build it with src/vector_store.py.")

    index = faiss.read_index(str(index_path))

    with open(chunks_path, "rb") as file:
        chunks = pickle.load(file)

    if index.ntotal != len(chunks) or not chunks:
        raise RuntimeError("PDF vector store index and metadata are empty or inconsistent.")
    return index, chunks


def search_documents(question, top_k=3, min_similarity=None):
    index, chunks = load_vector_store()
    if min_similarity is None:
        min_similarity = get_min_similarity()

    model = load_embedding_model()
    query_embedding = model.encode([question], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(query_embedding, top_k)
    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        if float(score) < min_similarity:
            continue
        results.append({
            "filename": chunks[idx]["filename"],
            "chunk_id": chunks[idx]["chunk_id"],
            "page_number": chunks[idx].get("page_number"),
            "text": chunks[idx]["text"],
            "similarity_score": float(score)
        })

    return results


if __name__ == "__main__":
    question = input("Enter your question: ")
    results = search_documents(question)

    print("\n========== SEARCH RESULTS ==========")
    for i, result in enumerate(results, start=1):
        print(f"\nResult {i}")
        print("PDF:", result["filename"])
        print("Chunk:", result["chunk_id"])
        print("Similarity:", round(result["similarity_score"], 4))
        print("Content:", result["text"])
