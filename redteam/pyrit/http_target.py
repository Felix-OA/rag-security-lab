"""Version-light HTTP adapter for use by a pinned PyRIT 0.14 integration."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx


@dataclass
class RAGLabTargetResult:
    scenario_id: str
    answer: str
    sources: list[dict[str, Any]]
    retrieved_chunks: list[dict[str, Any]]
    scores: list[float]
    trust_levels: list[str]
    flags: list[str]
    provider: str
    model: str
    security_profile: str
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RAGLabHTTPAdapter:
    """Preserve RAG-specific response metadata before mapping it into PyRIT memory.

    This adapter deliberately does not subclass a PyRIT target because that interface
    has changed across releases. The pinned integration layer should wrap this class
    and store ``to_dict()`` as auxiliary scenario evidence.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 45):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def send_prompt_async(self, question: str, scenario_id: str) -> RAGLabTargetResult:
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            retrieval_response = await client.get(
                f"{self.base_url}/debug/retrieval",
                params={"query": question},
            )
            retrieval_response.raise_for_status()
            retrieved_chunks = retrieval_response.json().get("chunks", [])
            response = await client.post(
                f"{self.base_url}/chat",
                json={"question": question},
                headers={"X-RAG-Lab-Scenario": scenario_id},
            )
            response.raise_for_status()
            payload = response.json()
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        sources = payload.get("sources", [])
        return RAGLabTargetResult(
            scenario_id=scenario_id,
            answer=payload.get("answer", ""),
            sources=sources,
            retrieved_chunks=retrieved_chunks,
            scores=[float(source.get("score", 0.0)) for source in sources],
            trust_levels=[str(source.get("trust_level", "unknown")) for source in sources],
            flags=payload.get("flags", []),
            provider=payload.get("provider", "unknown"),
            model=payload.get("model", "unknown"),
            security_profile=payload.get("security_profile", "unknown"),
            latency_ms=latency_ms,
        )
