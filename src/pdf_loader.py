from pathlib import Path

from pypdf import PdfReader


def extract_all_pdfs(data_folder=None):
    if data_folder is None:
        data_folder = Path(__file__).resolve().parent.parent / "data"
    else:
        data_folder = Path(data_folder)

    documents = []
    pdf_files = sorted(data_folder.glob("*.pdf"))

    for pdf_file in pdf_files:
        print(f"\nReading: {pdf_file.name}")

        reader = PdfReader(str(pdf_file))
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                pages.append({"page_number": page_number, "text": text})

        full_text = "\n".join(page["text"] for page in pages)
        documents.append({"filename": pdf_file.name, "text": full_text, "pages": pages})
        print(f"Pages: {len(reader.pages)}")
        print(f"Characters extracted: {len(full_text)}")

    return documents


if __name__ == "__main__":
    documents = extract_all_pdfs()

    print("\n========== EXTRACTION SUMMARY ==========")
    total_characters = 0

    for document in documents:
        total_characters += len(document["text"])
        print(f"{document['filename']} : {len(document['text'])} characters")

    print("\nTotal PDFs:", len(documents))
    print("Total characters:", total_characters)
