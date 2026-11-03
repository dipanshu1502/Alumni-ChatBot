from functools import lru_cache

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - runtime dependency may be unavailable
    SentenceTransformer = None

from process_documents import process_documents


@lru_cache(maxsize=1)
def load_embedding_model():
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is not available in the current Python environment.")

    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Embedding model loaded successfully!")
    return model


def generate_embeddings(chunks, model):
    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    return embeddings


if __name__ == "__main__":
    chunks = process_documents()
    model = load_embedding_model()
    embeddings = generate_embeddings(chunks, model)

    print("\n========== EMBEDDING SUMMARY ==========")
    print("Total chunks:", len(chunks))
    print("Embedding shape:", embeddings.shape)
    print("Vector dimensions:", embeddings.shape[1])
