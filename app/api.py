"""FastAPI endpoints for the vulnerable baseline RAG lab."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.filters import filter_output, filter_retrieval, inspect_input
from app.rag_pipeline import RAGPipeline

app = FastAPI(title="RAG Security Lab", version="0.1.0-baseline")
pipeline = RAGPipeline()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class Source(BaseModel):
    title: str
    path: str
    trust_level: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    flags: list[str]
    provider: str
    model: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "baseline-vulnerable"}


@app.get("/debug/retrieval")
def debug_retrieval(query: str = Query(min_length=1), top_k: int | None = Query(default=None, ge=1, le=20)) -> dict:
    try:
        chunks = pipeline.retrieve(query, top_k)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"query": query, "chunks": chunks}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    question, input_flags = inspect_input(request.question)
    try:
        retrieved = pipeline.retrieve(question)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    contexts, retrieval_flags = filter_retrieval(retrieved)
    answer, output_flags = filter_output(pipeline.answer(question, contexts))
    sources = [
        Source(
            title=item["metadata"]["title"],
            path=item["metadata"]["path"],
            trust_level=item["metadata"]["trust_level"],
            score=item["score"],
        )
        for item in contexts
    ]
    identity = pipeline.identity()
    return ChatResponse(
        answer=answer,
        sources=sources,
        flags=input_flags + retrieval_flags + output_flags,
        provider=identity["provider"],
        model=identity["model"],
    )
