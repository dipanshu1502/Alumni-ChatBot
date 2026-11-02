
def split_into_chunks(text, chunk_size=500, overlap=100):
    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


if __name__ == "__main__":

    sample_text = """
    Akal University provides various academic programs.
    Students can apply for undergraduate and postgraduate courses.
    The university also provides scholarships and placement support.
    """

    chunks = split_into_chunks(sample_text)

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {i} ---")
        print(chunk)
