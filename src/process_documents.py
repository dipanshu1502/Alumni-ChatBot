from chunking import split_into_chunks
from pdf_loader import extract_all_pdfs


def process_documents():
    documents = extract_all_pdfs()
    all_chunks = []

    for document in documents:
        filename = document["filename"]
        page_chunks = []
        if document.get("pages"):
            for page in document["pages"]:
                for chunk in split_into_chunks(page["text"], chunk_size=500, overlap=100):
                    page_chunks.append((page["page_number"], chunk))
        else:
            page_chunks = [(None, chunk) for chunk in split_into_chunks(document["text"], chunk_size=500, overlap=100)]

        for index, (page_number, chunk) in enumerate(page_chunks):
            all_chunks.append({"filename": filename, "page_number": page_number, "chunk_id": index, "text": chunk})

        print(f"{filename}: {len(page_chunks)} chunks created")

    return all_chunks


if __name__ == "__main__":
    chunks = process_documents()

    print("\n========== CHUNKING SUMMARY ==========")
    print("Total chunks:", len(chunks))

    if chunks:
        print("\nFirst chunk:")
        print(chunks[0]["text"])
