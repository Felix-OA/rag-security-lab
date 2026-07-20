# Controlled PyRIT setup

PyRIT is pinned to `0.14.0` in a separate environment because its target and scenario APIs evolve independently from the application.

```bash
python3.13 -m venv .venv-pyrit
source .venv-pyrit/bin/activate
python -m pip install -r redteam/pyrit/requirements.txt
python redteam/pyrit/run_pyrit_tests.py
```

With the API running locally, perform one controlled transport test:

```bash
python redteam/pyrit/run_pyrit_tests.py --smoke
```

Run the unchanged versioned custom suite and save deterministic evidence:

```bash
python redteam/pyrit/run_pyrit_tests.py --run
```

For a hardened retest, first verify/restart the API with `RAG_SECURITY_PROFILE=hardened`, then require that identity explicitly:

```bash
python redteam/pyrit/run_pyrit_tests.py --smoke --require-profile hardened
python redteam/pyrit/run_pyrit_tests.py --run \
  --require-profile hardened \
  --output reports/evidence/hardened-runs/hardened-pyrit-custom-<timestamp>.jsonl
```

`http_target.py` is a RAG-specific HTTP adapter. It preserves the answer, source objects, retrieved chunks, retrieval scores, trust levels, flags, provider/model identity, latency, and scenario ID. Raw JSONL is written under `reports/evidence/pyrit-runs/`. A future version-pinned PyRIT target wrapper can map the answer into a PyRIT assistant message while retaining this RAG-specific auxiliary evidence.

The primary evaluation path is deterministic: exact canary and poison markers, synthetic email and ID patterns, source trust, required facts, refusal terms, and unsupported-answer checks. An LLM judge may be added later as a secondary qualitative score, never as the only verdict.

Do not run multi-turn jailbreak automation or broad unsafe datasets for this project. Use the versioned local scenarios in `redteam/scenarios/baseline_scenarios.yaml`, and run only against this lab or another explicitly authorized target.
