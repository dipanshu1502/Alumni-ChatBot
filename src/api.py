from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Akal University AI Assistant API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


@app.get("/")
def home():
    return {"message": "Akal University AI Assistant API is running!"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Akal University AI Assistant"}


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        return {"answer": "Please enter a question.", "sources": []}

    try:
        from rag_pipeline import generate_answer

        result = generate_answer(question)
        return {
            "answer": result.get("answer", "I could not generate an answer."),
            "sources": result.get("sources", []),
        }
    except Exception as exc:  # pragma: no cover - defensive API fallback
        return {
            "answer": "Something went wrong while generating the answer. Please try again in a moment.",
            "sources": [],
            "error": str(exc),
        }