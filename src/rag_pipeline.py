from groq import Groq
from dotenv import load_dotenv
from retriever import search_documents

import os

# Load environment variables
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = os.getenv("GROQ_MODEL")


def generate_answer(question):

    # Step 1: Retrieve relevant PDF chunks
    results = search_documents(question, top_k=3)

    if not results:
        return {
            "answer": "I could not find relevant information in the documents.",
            "sources": []
        }

    # Step 2: Prepare context
    context = ""

    for result in results:
        context += f"""
Source: {result['filename']}

Content:
{result['text']}

---
"""

    # Step 3: Create prompt
    prompt = f"""
You are an AI assistant for Akal University.

Answer the user's question using ONLY the provided document context.

Rules:
1. Do not use outside knowledge.
2. If the answer is not available in the context, clearly say so.
3. Give clear and simple answers.
4. Do not invent dates, rules, or information.
5. Mention important steps as bullet points when appropriate.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    # Step 4: Generate answer using Groq
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    answer = response.choices[0].message.content

    # Step 5: Collect source filenames
    sources = list(set(
        result["filename"] for result in results
    ))

    return {
        "answer": answer,
        "sources": sources
    }


if __name__ == "__main__":

    question = input("\nAsk your question: ")

    result = generate_answer(question)

    print("\n========== AI ANSWER ==========")
    print(result["answer"])

    print("\n========== SOURCES ==========")

    for source in result["sources"]:
        print("-", source)