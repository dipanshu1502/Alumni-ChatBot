import streamlit as st
import sys
from pathlib import Path

# Import RAG pipeline
sys.path.append(str(Path(__file__).parent / "src"))

from rag_pipeline import generate_answer

# Page configuration
st.set_page_config(
    page_title="Akal University AI Assistant",
    page_icon="🎓",
    layout="centered"
)

# Custom heading
st.title("🎓 Akal University AI Assistant")
st.caption("Ask questions from university documents.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if "sources" in message:
            st.caption("Sources: " + ", ".join(message["sources"]))

# Chat input
question = st.chat_input("Ask your question...")

if question:

    # Display user question
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    # Generate AI response
    with st.chat_message("assistant"):

        with st.spinner("Searching university documents..."):

            try:
                result = generate_answer(question)

                answer = result["answer"]
                sources = result["sources"]

                st.markdown(answer)

                st.caption("Sources: " + ", ".join(sources))

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except Exception as e:
                st.error(f"Something went wrong: {e}")