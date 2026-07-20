"""Ingest synthetic Markdown documents into the local vector index."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from app.config import settings
from app.rag_pipeline import HashEmbedding, LocalVectorStore

COLLECTIONS = {
    "clean_docs": "trusted",
    "control_docs": "trusted",
    "poisoned_docs": "untrusted",
    "synthetic_pii_docs": "confidential",
}


def parse_document(path: Path, data_root: Path) -> dict:
    text = path.read_text(encoding="utf-8").strip()
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem.replace("_", " ").title()
    category = path.relative_to(data_root).parts[0]
    classification_match = re.search(r"^Classification:\s*(.+)$", text, flags=re.MULTILINE | re.IGNORECASE)
    allowed_role_match = re.search(r"^Allowed access role:\s*(.+)$", text, flags=re.MULTILINE | re.IGNORECASE)
    default_classification = {
        "clean_docs": "public policy",
        "control_docs": "trusted control",
        "poisoned_docs": "untrusted reference",
        "synthetic_pii_docs": "confidential synthetic fixture",
    }[category]
    return {
        "title": title,
        "path": str(path.relative_to(data_root.parent)),
        "trust_level": COLLECTIONS[category],
        "classification": (
            classification_match.group(1).strip() if classification_match else default_classification
        ),
        "allowed_roles": (
            [role.strip() for role in allowed_role_match.group(1).split(",") if role.strip()]
            if allowed_role_match
            else []
        ),
        "source_type": category,
        "text": text,
    }


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("chunk size must be positive and overlap must be between 0 and size")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind("\n", start, end)
            if boundary > start + size // 2:
                end = boundary
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = end - overlap
    return [chunk for chunk in chunks if chunk]


def collect_chunks(data_root: Path, chunk_size: int, chunk_overlap: int) -> list[dict]:
    records: list[dict] = []
    for folder, trust_level in COLLECTIONS.items():
        directory = data_root / folder
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            document = parse_document(path, data_root)
            assert document["trust_level"] == trust_level
            for index, chunk in enumerate(chunk_text(document["text"], chunk_size, chunk_overlap)):
                records.append(
                    {
                        "id": f"{folder}:{path.stem}:{index}",
                        "text": chunk,
                        "metadata": {
                            "title": document["title"],
                            "path": document["path"],
                            "trust_level": trust_level,
                            "classification": document["classification"],
                            "allowed_roles": document["allowed_roles"],
                            "source_type": document["source_type"],
                            "chunk_index": index,
                        },
                    }
                )
    return records


def build_index(data_root: Path | None = None, index_dir: Path | None = None) -> dict:
    data_root = data_root or settings.data_dir
    index_dir = index_dir or settings.index_dir
    records = collect_chunks(data_root, settings.chunk_size, settings.chunk_overlap)
    if not records:
        raise RuntimeError(f"No Markdown documents found under {data_root}")
    store = LocalVectorStore(index_dir, HashEmbedding(settings.embedding_dimensions))
    backend = store.build(records)
    summary = {
        "documents": len({record["metadata"]["path"] for record in records}),
        "chunks": len(records),
        "backend": backend,
        "index_dir": str(index_dir),
    }
    (index_dir / "ingestion_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=settings.data_dir)
    parser.add_argument("--index-dir", type=Path, default=settings.index_dir)
    args = parser.parse_args()
    print(json.dumps(build_index(args.data_dir, args.index_dir), indent=2))


if __name__ == "__main__":
    main()
