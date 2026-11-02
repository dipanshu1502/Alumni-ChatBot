
from pathlib import Path
from pypdf import PdfReader


def extract_all_pdfs(data_folder="data"):

    pdf_folder = Path(data_folder)
    documents = []

    pdf_files = sorted(pdf_folder.glob("*.pdf"))

    for pdf_file in pdf_files:

        print(f"\nReading: {pdf_file.name}")

        reader = PdfReader(str(pdf_file))
        full_text = ""

        for page_number, page in enumerate(reader.pages, start=1):

            text = page.extract_text()

            if text:
                full_text += text + "\n"

        documents.append({
            "filename": pdf_file.name,
            "text": full_text
        })

        print(f"Pages: {len(reader.pages)}")
        print(f"Characters extracted: {len(full_text)}")

    return documents


if __name__ == "__main__":

    documents = extract_all_pdfs()

    print("\n========== EXTRACTION SUMMARY ==========")

    total_characters = 0

    for document in documents:
        total_characters += len(document["text"])

        print(
            f"{document['filename']} : "
            f"{len(document['text'])} characters"
        )

    print("\nTotal PDFs:", len(documents))
    print("Total characters:", total_characters)
