"""Retrieval and generation components for the baseline RAG application."""

from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.config import Settings, settings
from app.prompts import BASIC_RAG_SYSTEM_PROMPT, HARDENED_RAG_SYSTEM_PROMPT, build_user_prompt


class HashEmbedding:
    """Small deterministic bag-of-words embedding suitable only for this demo."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[a-z0-9_@.]+", text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[slot] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class LocalVectorStore:
    """Persist records locally and use FAISS when installed, with a cosine fallback."""

    def __init__(self, index_dir: Path, embedder: HashEmbedding):
        self.index_dir = index_dir
        self.embedder = embedder
        self.records: list[dict] = []
        self.vectors: list[list[float]] = []
        self._faiss_index: Any | None = None

    @property
    def records_path(self) -> Path:
        return self.index_dir / "records.json"

    def build(self, records: list[dict]) -> str:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.records = records
        self.vectors = [self.embedder.embed(record["text"]) for record in records]
        payload = {"dimensions": self.embedder.dimensions, "records": records, "vectors": self.vectors}
        self.records_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            import faiss  # type: ignore
            import numpy as np  # type: ignore

            index = faiss.IndexFlatIP(self.embedder.dimensions)
            index.add(np.asarray(self.vectors, dtype="float32"))
            faiss.write_index(index, str(self.index_dir / "index.faiss"))
            self._faiss_index = index
            return "faiss"
        except ImportError:
            return "portable-cosine-fallback"

    def load(self) -> None:
        if not self.records_path.exists():
            raise FileNotFoundError("Vector index is missing. Run: python -m app.ingest")
        payload = json.loads(self.records_path.read_text(encoding="utf-8"))
        if payload.get("dimensions") != self.embedder.dimensions:
            raise ValueError(
                "Embedding dimensions differ from the persisted index. Run: python -m app.ingest"
            )
        self.records = payload["records"]
        self.vectors = payload["vectors"]
        try:
            import faiss  # type: ignore

            faiss_path = self.index_dir / "index.faiss"
            if faiss_path.exists():
                self._faiss_index = faiss.read_index(str(faiss_path))
        except ImportError:
            self._faiss_index = None

    def search(self, query: str, top_k: int) -> list[dict]:
        if not self.records:
            self.load()
        query_vector = self.embedder.embed(query)
        if self._faiss_index is not None:
            import numpy as np  # type: ignore

            scores, indices = self._faiss_index.search(np.asarray([query_vector], dtype="float32"), top_k)
            ranked = [(int(index), float(score)) for index, score in zip(indices[0], scores[0]) if index >= 0]
        else:
            ranked = sorted(
                enumerate(sum(a * b for a, b in zip(query_vector, vector)) for vector in self.vectors),
                key=lambda pair: pair[1],
                reverse=True,
            )[:top_k]
        return [{**self.records[index], "score": round(score, 6)} for index, score in ranked]


class ModelClient:
    def __init__(self, config: Settings | Any | None = None):
        self.config = config or settings

    @property
    def provider(self) -> str:
        return self.config.model_provider

    @property
    def model(self) -> str:
        return self.config.model_name

    def generate(self, system_prompt: str, user_prompt: str, contexts: list[dict]) -> str:
        if self.config.model_provider == "extractive":
            if not contexts:
                return "I do not know based on the retrieved context."
            # Intentionally weak: echoes the most relevant context without redaction.
            excerpt = contexts[0]["text"].replace("\n", " ")[:700]
            return f"Based on the retrieved context: {excerpt}"
        if self.config.model_provider != "openai_compatible":
            raise ValueError("MODEL_PROVIDER must be 'extractive' or 'openai_compatible'")
        body = json.dumps(
            {
                "model": self.config.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": self.config.model_temperature,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        request = urllib.request.Request(
            f"{self.config.api_base_url.rstrip('/')}/chat/completions", data=body, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.request_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"]
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI-compatible model request failed: {exc}") from exc


class RAGPipeline:
    def __init__(self, index_dir: Path | None = None, config: Settings | None = None):
        self.config = config or settings
        self.store = LocalVectorStore(
            index_dir or self.config.index_dir,
            HashEmbedding(self.config.embedding_dimensions),
        )
        self.model = ModelClient(self.config)

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        return self.store.search(query, top_k or self.config.top_k)

    def answer(self, question: str, contexts: list[dict]) -> str:
        hardened = self.config.security_profile == "hardened"
        system_prompt = HARDENED_RAG_SYSTEM_PROMPT if hardened else BASIC_RAG_SYSTEM_PROMPT
        return self.model.generate(
            system_prompt,
            build_user_prompt(question, contexts, hardened=hardened),
            contexts,
        )

    def identity(self) -> dict[str, str]:
        return {
            "provider": self.model.provider,
            "model": self.model.model,
            "security_profile": self.config.security_profile,
        }
