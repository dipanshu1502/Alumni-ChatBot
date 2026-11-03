import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent / "src"))

from rag_pipeline import generate_answer

st.set_page_config(
    page_title="Akal University AI Assistant",
    page_icon="🎓",
    layout="centered",
)

st.title("🎓 Akal University AI Assistant")
st.caption("Ask questions about university documents, rules, and alumni portal information.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            st.caption("Sources: " + ", ".join(message["sources"]))

question = st.chat_input("Ask your question...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching university documents and live knowledge sources..."):
            try:
                result = generate_answer(question)
                answer = result.get("answer", "I could not generate an answer.")
                sources = result.get("sources", [])
                st.markdown(answer)
                if sources:
                    st.caption("Sources: " + ", ".join(sources))
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })
            except Exception as exc:
                st.error(f"Something went wrong: {exc}")