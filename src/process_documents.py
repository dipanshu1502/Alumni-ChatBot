
from pdf_loader import extract_all_pdfs
from chunking import split_into_chunks


def process_documents():

    documents = extract_all_pdfs()

    all_chunks = []

    for document in documents:

        filename = document["filename"]
        text = document["text"]

        chunks = split_into_chunks(
            text,
            chunk_size=500,
            overlap=100
        )

        for index, chunk in enumerate(chunks):

            all_chunks.append({
                "filename": filename,
                "chunk_id": index,
                "text": chunk
            })

        print(f"{filename}: {len(chunks)} chunks created")

    return all_chunks


if __name__ == "__main__":

    chunks = process_documents()

    print("\n========== CHUNKING SUMMARY ==========")
    print("Total chunks:", len(chunks))

    if chunks:
        print("\nFirst chunk:")
        print(chunks[0]["text"])
