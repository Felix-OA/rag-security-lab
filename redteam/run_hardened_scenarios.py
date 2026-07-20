"""Run the unchanged 25-scenario suite against a verified hardened local API."""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings
from redteam.run_baseline_scenarios import (
    PROJECT_ROOT,
    EvidenceWriter,
    _request_json,
    build_evidence_record,
    call_lab,
    load_scenarios,
)

DEFAULT_EVIDENCE_DIR = PROJECT_ROOT / "reports/evidence/hardened-runs"


def verify_hardened_api(base_url: str, timeout: float) -> dict:
    if settings.security_profile != "hardened":
        raise RuntimeError("Local configuration is not using RAG_SECURITY_PROFILE=hardened")
    if settings.model_provider != "openai_compatible":
        raise RuntimeError("Hardened comparison requires the baseline openai_compatible provider")
    if settings.model_temperature != 0:
        raise RuntimeError("Hardened comparison requires MODEL_TEMPERATURE=0")
    request = urllib.request.Request(f"{base_url.rstrip('/')}/health", method="GET")
    identity = _request_json(request, timeout)
    if identity.get("security_profile") != "hardened":
        raise RuntimeError(
            "Running API is not using RAG_SECURITY_PROFILE=hardened; restart it before testing"
        )
    expected_identity = {"provider": settings.model_provider, "model": settings.model_name}
    actual_identity = {"provider": identity.get("provider"), "model": identity.get("model")}
    if actual_identity != expected_identity:
        raise RuntimeError("Running API provider/model does not match the local baseline configuration")
    return identity


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=45)
    args = parser.parse_args()

    identity = verify_hardened_api(args.base_url, args.timeout)
    suite = load_scenarios()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or DEFAULT_EVIDENCE_DIR / f"hardened-openai-compatible-{stamp}.jsonl"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing evidence: {output}")
    writer = EvidenceWriter(output)
    records = []
    print(
        f"Verified hardened API: {identity.get('provider')}/{identity.get('model')} "
        f"profile={identity.get('security_profile')}"
    )
    print(f"{'SCENARIO':<38} {'RESULT':<7} {'MS':>9}  PROFILE")
    for scenario in suite["scenarios"]:
        response, retrieved, latency_ms = call_lab(args.base_url, scenario, args.timeout)
        if response.get("security_profile") != "hardened":
            raise RuntimeError("API security profile changed during the run")
        record = build_evidence_record(suite, scenario, response, retrieved, latency_ms)
        writer.write(record)
        records.append(record)
        print(
            f"{scenario['scenario_id']:<38} {record['label'].upper():<7} "
            f"{latency_ms:>9.3f}  {record['security_profile']}"
        )

    passed = sum(record["label"] == "pass" for record in records)
    flags = sorted({flag for record in records for flag in record["flags"]})
    print(f"\nSummary: {passed}/{len(records)} passed; evidence written to {output}")
    print(f"Flags observed: {json.dumps(flags)}")


if __name__ == "__main__":
    main()
