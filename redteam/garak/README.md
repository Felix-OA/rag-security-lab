# Controlled garak setup

This integration is scoped to the local RAG lab. The template targets garak `0.15.1`; garak configuration is version-sensitive, so inspect the installed plugin before running it.

## Separate environment

Python 3.12 is recommended for garak. From the project root:

```bash
python3.12 -m venv .venv-garak
source .venv-garak/bin/activate
python -m pip install -r redteam/garak/requirements.txt
garak --version
garak --plugin_info generators.rest.RestGenerator
cp redteam/garak/garak_config.yaml.example redteam/garak/garak_config.yaml
```

Do not put keys in the YAML. This local endpoint requires none.

## Connectivity before probes

Start the lab with an explicitly selected provider, then confirm one request:

```bash
curl -s http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the current refund window?"}'
```

Check that the response includes `answer`, `sources`, `provider`, and `model`. Run extractive mode only to validate transport. Use a configured `openai_compatible` LLM for claims about instruction compliance.

## Narrow initial run

After confirming the installed option names against `--plugin_info`:

```bash
garak --config redteam/garak/garak_config.yaml
```

The template limits the first run to two harmless tier-1 latent-injection snippet probes with a six-prompt cap, one generation, and no parallelism. The built-in `promptinject` family is excluded because its payload themes are outside this lab's approved narrow scope. Generic garak probes are supplemental: they do not prove that a seeded poisoned document was retrieved. The project-specific scenario runner is the primary source of RAG retrieval and leakage evidence.

Out of scope: `all` scans, generic jailbreak collections, malware generation, toxicity/extremist suites, resource-exhaustion or high-concurrency tests, and every public or third-party target. Only assess systems you own or have explicit written authorization to test.

Save raw garak output under `reports/evidence/garak-runs/` and record tool version, model identity, configuration, timestamp, and corpus version in the baseline report.
