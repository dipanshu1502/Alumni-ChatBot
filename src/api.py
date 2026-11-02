from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create FastAPI application
app = FastAPI(
    title="Akal University AI Assistant API",
    version="1.0.0"
)

# Allow React frontend to communicate with Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request structure
class ChatRequest(BaseModel):
    question: str


# Home route
@app.get("/")
def home():
    return {
        "message": "Akal University AI Assistant API is running!"
    }


# Chat API
@app.post("/chat")
def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:
        return {
            "answer": "Please enter a question.",
            "sources": []
        }

    try:
        from rag_pipeline import generate_answer

        result = generate_answer(question)

        return {
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:
        return {
            "answer": "Something went wrong while generating the answer.",
            "sources": [],
            "error": str(e)
        }