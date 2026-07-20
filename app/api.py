"""FastAPI endpoints for the switchable baseline/hardened RAG lab."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.filters import (
    CONFIDENTIAL_REFUSAL,
    filter_output,
    filter_retrieval,
    inspect_input,
    is_confidential_request,
)
from app.rag_pipeline import ModelProviderError, RAGPipeline

app = FastAPI(title="RAG Security Lab", version="0.2.0-bounded-hardening")
pipeline = RAGPipeline()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    role: str = Field(default="general", min_length=1, max_length=80, pattern=r"^[a-z0-9_-]+$")
    role_verified: bool = Field(
        default=False,
        description="Local test fixture only; simulates a role already verified by trusted middleware.",
    )


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
    security_profile: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.2.0", **pipeline.identity()}


@app.get("/debug/retrieval")
def debug_retrieval(query: str = Query(min_length=1), top_k: int | None = Query(default=None, ge=1, le=20)) -> dict:
    try:
        chunks = pipeline.retrieve(query, top_k)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"query": query, "chunks": chunks, "security_profile": pipeline.config.security_profile}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    profile = pipeline.config.security_profile
    question, input_flags = inspect_input(
        request.question,
        role=request.role,
        role_verified=request.role_verified,
        security_profile=profile,
    )
    try:
        retrieved = pipeline.retrieve(question)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    contexts, retrieval_flags = filter_retrieval(
        retrieved,
        role=request.role,
        role_verified=request.role_verified,
        security_profile=profile,
    )
    blocked = "confidential_request_blocked" in input_flags
    if is_confidential_request(question) and "unauthorized_confidential_access" in retrieval_flags:
        blocked = True
        input_flags.append("confidential_request_blocked")
    try:
        generated = CONFIDENTIAL_REFUSAL if blocked else pipeline.answer(question, contexts)
    except ModelProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    answer, output_flags = filter_output(generated, security_profile=profile)
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
        flags=list(dict.fromkeys(input_flags + retrieval_flags + output_flags)),
        provider=identity["provider"],
        model=identity["model"],
        security_profile=identity["security_profile"],
    )
