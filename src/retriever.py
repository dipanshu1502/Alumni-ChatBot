import faiss
import pickle
import numpy as np
from functools import lru_cache
from pathlib import Path
from embeddings import load_embedding_model

@lru_cache(maxsize=1)
def load_vector_store():
    storage_folder = Path("vector_db")

    index = faiss.read_index(
        str(storage_folder / "index.faiss")
    )

    with open(storage_folder / "chunks.pkl", "rb") as file:
        chunks = pickle.load(file)

    return index, chunks

def load_vector_store():
    storage_folder = Path("vector_db")

    # Load FAISS index
    index = faiss.read_index(
        str(storage_folder / "index.faiss")
    )

    # Load PDF chunks
    with open(storage_folder / "chunks.pkl", "rb") as file:
        chunks = pickle.load(file)

    return index, chunks


def search_documents(question, top_k=3):

    # Load saved vector database
    index, chunks = load_vector_store()

    # Load embedding model
    model = load_embedding_model()

    # Convert user question into embedding
    query_embedding = model.encode(
        [question],
        convert_to_numpy=True
    ).astype("float32")

    # Normalize query vector
    faiss.normalize_L2(query_embedding)

    # Search similar vectors
    scores, indices = index.search(query_embedding, top_k)

    results = []

    for score, idx in zip(scores[0], indices[0]):

        if idx == -1:
            continue

        results.append({
            "filename": chunks[idx]["filename"],
            "chunk_id": chunks[idx]["chunk_id"],
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