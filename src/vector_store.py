import pickle
from pathlib import Path

import faiss

from embeddings import generate_embeddings, load_embedding_model
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

    storage_folder = Path(__file__).resolve().parent.parent / "vector_db"
    storage_folder.mkdir(exist_ok=True)

    faiss.write_index(index, str(storage_folder / "index.faiss"))

    with open(storage_folder / "chunks.pkl", "wb") as file:
        pickle.dump(chunks, file)

    print("\n========== VECTOR STORE SAVED ==========")
    print("Total vectors:", index.ntotal)
    print("Storage folder:", storage_folder)

    return index, chunks


if __name__ == "__main__":
    create_vector_store()