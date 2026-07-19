"""Environment-backed configuration for the local lab."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
    index_dir: Path = Path(os.getenv("INDEX_DIR", str(PROJECT_ROOT / ".rag_index")))
    top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))
    model_provider: str = os.getenv("MODEL_PROVIDER", "extractive")
    model_name: str = os.getenv("MODEL_NAME", "local-extractive-demo")
    api_base_url: str = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    request_timeout: float = float(os.getenv("MODEL_TIMEOUT_SECONDS", "30"))
    model_temperature: float = float(os.getenv("MODEL_TEMPERATURE", "0"))

    def __post_init__(self) -> None:
        if self.model_provider not in {"extractive", "openai_compatible"}:
            raise ValueError("MODEL_PROVIDER must be 'extractive' or 'openai_compatible'")
        if self.top_k <= 0:
            raise ValueError("RAG_TOP_K must be positive")
        if self.chunk_size <= 0 or not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("RAG chunk size/overlap configuration is invalid")
        if self.embedding_dimensions <= 0:
            raise ValueError("EMBEDDING_DIMENSIONS must be positive")
        if self.model_temperature < 0:
            raise ValueError("MODEL_TEMPERATURE cannot be negative")


settings = Settings()
