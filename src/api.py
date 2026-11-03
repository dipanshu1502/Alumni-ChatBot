import logging
import os
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

app = FastAPI(
    title="Akal University AI Assistant API",
    version="1.0.0",
)
log = logging.getLogger("chatbot.api")

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
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be blank.")
        return value


@app.get("/")
def home():
    return {"message": "Akal University AI Assistant API is running!"}


@app.get("/health")
def health():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    try:
        from retriever import load_vector_store
        load_vector_store()
        vector_store_status = "ready"
    except Exception:
        log.exception("PDF vector store readiness check failed")
        vector_store_status = "unavailable"

    groq_status = "ready" if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_MODEL") else "not_configured"
    portal_status = "unavailable"
    try:
        base_url = (os.getenv("CI4_API_BASE_URL") or "http://localhost:8080/api").rstrip("/")
        response = requests.get(f"{base_url}/public/stats", timeout=(1, 2))
        response.raise_for_status()
        if "json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("Portal health endpoint did not return JSON")
        portal_status = "ready"
    except Exception:
        log.info("Portal readiness check failed", exc_info=True)

    checks = {
        "groq": groq_status,
        "documents": vector_store_status,
        "portal": portal_status,
    }
    ready = checks["groq"] == "ready" and any(
        checks[source] == "ready" for source in ("documents", "portal")
    )
    return {
        "status": "ok" if ready else "degraded",
        "service": "Akal University AI Assistant",
        "checks": checks,
    }


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()
    if not question:
        return {"answer": "Please enter a question.", "sources": []}

    try:
        from rag_pipeline import generate_answer

        result = generate_answer(question)
        if result.get("status") == "unavailable":
            raise HTTPException(status_code=503, detail=result["answer"])
        return {
            "answer": result.get("answer", "I could not generate an answer."),
            "sources": result.get("sources", []),
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive API fallback
        log.exception("Chat answer generation failed")
        raise HTTPException(
            status_code=503,
            detail="Answer generation is temporarily unavailable. Please try again.",
        ) from exc
