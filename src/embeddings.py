from functools import lru_cache
from sentence_transformers import SentenceTransformer
from process_documents import process_documents

@lru_cache(maxsize=1)
def load_embedding_model():
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Embedding model loaded successfully!")
    return model


def load_embedding_model():

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

    # Load all PDF chunks
    chunks = process_documents()

    # Load embedding model
    model = load_embedding_model()

    # Generate embeddings
    embeddings = generate_embeddings(chunks, model)

    print("\n========== EMBEDDING SUMMARY ==========")
    print("Total chunks:", len(chunks))
    print("Embedding shape:", embeddings.shape)
    print("Vector dimensions:", embeddings.shape[1])
