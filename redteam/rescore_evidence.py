"""Re-score immutable JSONL evidence into a separate compact comparison file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from redteam.run_baseline_scenarios import load_scenarios
from redteam.scorers import SCORER_VERSION, score_response


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite existing re-score output: {args.output}")

    scenarios = {item["scenario_id"]: item for item in load_scenarios()["scenarios"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.input.open(encoding="utf-8") as source, args.output.open("x", encoding="utf-8") as target:
        for line in source:
            record = json.loads(line)
            scenario = scenarios[record["scenario_id"]]
            scoring = score_response(scenario, record, record.get("retrieved_chunks", []))
            compact = {
                "scenario_id": record["scenario_id"],
                "original_label": record.get("label"),
                "rescored_label": "pass" if scoring["passed"] else "fail",
                "scorer_version": SCORER_VERSION,
                "signals": scoring["signals"],
            }
            target.write(json.dumps(compact, sort_keys=True) + "\n")
    print(f"Wrote scorer {SCORER_VERSION} comparison to {args.output}; raw evidence was not modified.")


if __name__ == "__main__":
    main()
