"""Run the narrow custom RAG suite through the version-light PyRIT adapter."""

from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from redteam.pyrit.http_target import RAGLabHTTPAdapter
from redteam.run_baseline_scenarios import load_scenarios
from redteam.scorers import score_response

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE_DIR = PROJECT_ROOT / "reports/evidence/pyrit-runs"


def pyrit_version() -> str:
    try:
        return importlib.metadata.version("pyrit")
    except importlib.metadata.PackageNotFoundError:
        return "adapter-only (PyRIT package not installed)"


async def smoke_test(base_url: str) -> None:
    suite = load_scenarios()
    scenario = suite["scenarios"][0]
    result = await RAGLabHTTPAdapter(base_url).send_prompt_async(
        scenario["user_question"], scenario["scenario_id"]
    )
    print(
        f"Smoke test received provider={result.provider}, model={result.model}, "
        f"sources={len(result.sources)}, latency_ms={result.latency_ms}"
    )


async def run_suite(base_url: str, output: Path) -> list[dict]:
    suite = load_scenarios()
    adapter = RAGLabHTTPAdapter(base_url)
    output.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    with output.open("x", encoding="utf-8") as handle:
        for scenario in suite["scenarios"]:
            result = await adapter.send_prompt_async(scenario["user_question"], scenario["scenario_id"])
            response = {
                "answer": result.answer,
                "sources": result.sources,
                "flags": result.flags,
            }
            scoring = score_response(scenario, response, result.retrieved_chunks)
            record = {
                "schema_version": suite["schema_version"],
                "suite_name": suite["suite_name"],
                "tool": "pyrit-http-adapter",
                "pyrit_version": pyrit_version(),
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "scenario_id": scenario["scenario_id"],
                "category": scenario["category"],
                "question": scenario["user_question"],
                "answer": result.answer,
                "sources": result.sources,
                "retrieved_chunks": result.retrieved_chunks,
                "provider": result.provider,
                "model": result.model,
                "flags": result.flags,
                "latency_ms": result.latency_ms,
                "scoring": scoring,
                "label": "pass" if scoring["passed"] else "fail",
            }
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            records.append(record)
            print(
                f"{scenario['scenario_id']:<38} {record['label'].upper():<7} "
                f"{result.latency_ms:>9.3f}  {result.provider}/{result.model}"
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="Send one request to the running local lab")
    parser.add_argument("--run", action="store_true", help="Run all versioned custom RAG scenarios")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    suite = load_scenarios()
    print(
        f"PyRIT version: {pyrit_version()}; validated "
        f"{len(suite['scenarios'])} versioned synthetic scenarios."
    )
    if args.smoke:
        asyncio.run(smoke_test(args.base_url))
    elif args.run:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output = args.output or DEFAULT_EVIDENCE_DIR / f"pyrit-custom-baseline-{stamp}.jsonl"
        records = asyncio.run(run_suite(args.base_url, output))
        passed = sum(record["label"] == "pass" for record in records)
        print(f"Summary: {passed}/{len(records)} passed; evidence written to {output}")
    else:
        print("No requests sent. Add --smoke or --run after starting the local lab.")


if __name__ == "__main__":
    main()
