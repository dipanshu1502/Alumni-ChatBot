import faiss
import numpy as np
import pickle
from pathlib import Path

from embeddings import load_embedding_model, generate_embeddings
from process_documents import process_documents


def create_vector_store():
    chunks = process_documents()

    model = load_embedding_model()
    embeddings = generate_embeddings(chunks, model)

    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    # Create storage folder
    storage_folder = Path("vector_db")
    storage_folder.mkdir(exist_ok=True)

    # Save FAISS index
    faiss.write_index(index, str(storage_folder / "index.faiss"))

    # Save original chunks and metadata
    with open(storage_folder / "chunks.pkl", "wb") as file:
        pickle.dump(chunks, file)

    print("\n========== VECTOR STORE SAVED ==========")
    print("Total vectors:", index.ntotal)
    print("Storage folder:", storage_folder)

    return index, chunks


if __name__ == "__main__":
    create_vector_store()