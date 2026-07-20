"""Run versioned baseline scenarios against the local RAG API and save JSONL evidence."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from redteam.scorers import score_response

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = PROJECT_ROOT / "redteam/scenarios/baseline_scenarios.yaml"
DEFAULT_EVIDENCE_DIR = PROJECT_ROOT / "reports/evidence/baseline-runs"


class EvidenceWriter:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def load_scenarios(path: Path = DEFAULT_SCENARIOS) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("scenarios"), list):
        raise ValueError("Scenario file must contain a top-level scenarios list")
    required = {
        "scenario_id",
        "name",
        "category",
        "user_question",
        "expected_behavior",
        "forbidden_substrings",
        "required_absent_patterns",
        "expected_result_type",
        "notes",
    }
    seen: set[str] = set()
    for scenario in payload["scenarios"]:
        missing = required - set(scenario)
        if missing:
            raise ValueError(f"Scenario is missing required fields: {sorted(missing)}")
        scenario_id = scenario["scenario_id"]
        if scenario_id in seen:
            raise ValueError(f"Duplicate scenario_id: {scenario_id}")
        seen.add(scenario_id)
    return payload


def _request_json(request: urllib.request.Request, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Local RAG API request failed: {exc}") from exc


def call_lab(base_url: str, scenario: dict[str, Any], timeout: float) -> tuple[dict, list[dict], float]:
    question = scenario["user_question"]
    debug_url = f"{base_url.rstrip('/')}/debug/retrieval?{urllib.parse.urlencode({'query': question})}"
    debug_request = urllib.request.Request(debug_url, method="GET")
    retrieved = _request_json(debug_request, timeout).get("chunks", [])

    body = json.dumps({"question": question}).encode("utf-8")
    chat_request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat",
        data=body,
        headers={"Content-Type": "application/json", "X-RAG-Lab-Scenario": scenario["scenario_id"]},
        method="POST",
    )
    started = time.perf_counter()
    response = _request_json(chat_request, timeout)
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    return response, retrieved, latency_ms


def build_evidence_record(
    suite: dict[str, Any], scenario: dict[str, Any], response: dict[str, Any], retrieved: list[dict], latency_ms: float
) -> dict[str, Any]:
    scoring = score_response(scenario, response, retrieved)
    return {
        "schema_version": suite["schema_version"],
        "suite_name": suite["suite_name"],
        "scenario_id": scenario["scenario_id"],
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "category": scenario["category"],
        "question": scenario["user_question"],
        "answer": response.get("answer", ""),
        "sources": response.get("sources", []),
        "source_trust_levels": [source.get("trust_level") for source in response.get("sources", [])],
        "retrieved_chunks": retrieved,
        "provider": response.get("provider", "unknown"),
        "model": response.get("model", "unknown"),
        "security_profile": response.get("security_profile", "unknown"),
        "scorer_version": scoring["scorer_version"],
        "flags": response.get("flags", []),
        "latency_ms": latency_ms,
        "scoring": scoring,
        "label": "pass" if scoring["passed"] else "fail",
        "expected_behavior": scenario["expected_behavior"],
        "notes": scenario["notes"],
    }


def write_markdown_summary(path: Path, records: list[dict[str, Any]], evidence_path: Path) -> None:
    passed = sum(record["label"] == "pass" for record in records)
    categories = Counter(record["category"] for record in records)
    failures = [record for record in records if record["label"] == "fail"]
    lines = [
        "# Baseline Findings",
        "",
        f"Run timestamp: {datetime.now(UTC).isoformat()}",
        f"Evidence: `{evidence_path.relative_to(PROJECT_ROOT)}`",
        f"Result: {passed}/{len(records)} scenarios passed deterministic baseline expectations.",
        "",
        "## Scenario counts",
        "",
    ]
    lines.extend(f"- {category}: {count}" for category, count in sorted(categories.items()))
    lines.extend(["", "## Deterministic failures", ""])
    lines.extend(f"- `{record['scenario_id']}`: {record['expected_behavior']}" for record in failures)
    lines.extend(
        [
            "",
            "> Results apply only to this synthetic configuration and are not a security certification.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=45)
    parser.add_argument("--write-markdown", action="store_true")
    args = parser.parse_args()

    suite = load_scenarios(args.scenarios)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or DEFAULT_EVIDENCE_DIR / f"baseline-{stamp}.jsonl"
    writer = EvidenceWriter(output)
    records = []
    print(f"{'SCENARIO':<38} {'RESULT':<7} {'MS':>9}  PROVIDER/MODEL")
    for scenario in suite["scenarios"]:
        response, retrieved, latency_ms = call_lab(args.base_url, scenario, args.timeout)
        record = build_evidence_record(suite, scenario, response, retrieved, latency_ms)
        writer.write(record)
        records.append(record)
        print(
            f"{scenario['scenario_id']:<38} {record['label'].upper():<7} "
            f"{latency_ms:>9.3f}  {record['provider']}/{record['model']}"
        )

    passed = sum(record["label"] == "pass" for record in records)
    print(f"\nSummary: {passed}/{len(records)} passed; evidence written to {output}")
    if args.write_markdown:
        write_markdown_summary(PROJECT_ROOT / "reports/baseline-findings.md", records, output)
        print("Updated reports/baseline-findings.md")


if __name__ == "__main__":
    main()
