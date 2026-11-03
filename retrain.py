"""Rebuild the chatbot's PDF knowledge index.

Run from any working directory with:
    python retrain.py

This refreshes document chunks and embeddings; it does not fine-tune the
hosted Groq language model.
"""

import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"
DATA_DIR = PROJECT_DIR / "data"


def main() -> int:
    if not DATA_DIR.is_dir() or not any(DATA_DIR.glob("*.pdf")):
        print(f"No PDF files found in: {DATA_DIR}")
        return 1

    sys.path.insert(0, str(SRC_DIR))

    try:
        from vector_store import create_vector_store

        index, chunks = create_vector_store()
    except Exception as exc:
        print(f"Knowledge index rebuild failed: {exc}")
        return 1

    print("\nKnowledge index rebuilt successfully.")
    print(f"PDF chunks indexed: {len(chunks)}")
    print(f"FAISS vectors: {index.ntotal}")
    print(f"Index location: {PROJECT_DIR / 'vector_db'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
