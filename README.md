# RAG Security Lab

**Status: Bounded hardening implementation phase.**

RAG Security Lab is an intentionally vulnerable, local retrieval-augmented question-answering API for controlled measurement of retrieval poisoning, indirect prompt injection, synthetic PII and canary leakage, source-trust confusion, confidential-document exposure, and grounding failures. The planned case study is baseline test → targeted hardening → identical retest → before/after analysis.

> **Responsible use:** This repository is a controlled educational test environment. Run assessments only against the included local service or another system for which you have explicit written authorization. The synthetic canaries are designed solely for measurement and must never be replaced with production credentials, customer records, or personal data. The results demonstrate behavior in this test configuration only and are not a security certification.

This is not secure RAG, is not enterprise-ready, and is not certified by garak, PyRIT, or any other tool.

## Security profiles

`RAG_SECURITY_PROFILE` selects a comparison profile. The default is `baseline` so historical behavior is not silently changed.

- `baseline`: retrieves top-k chunks without enforcing source trust, places trusted, untrusted, and confidential material into context, and returns the answer without PII/canary redaction. This intentionally vulnerable behavior is preserved for regression comparison.
- `hardened`: enables bounded controls for this synthetic lab: confidential-context access decisions, deterministic confidentiality refusal, trusted-source preference, instruction-like untrusted-content filtering, prompt isolation, and output canary/PII redaction.

The hardened profile does not guarantee prompt-injection prevention, complete PII detection, authentication, compliance, certification, or production readiness.

Two provider modes are available:

- `extractive`: deterministic, key-free fallback that returns an excerpt from the highest-ranked chunk. It measures retrieval exposure and direct content echo only. **It is not an LLM and its output must not be described as indirect prompt-injection compliance.**
- `openai_compatible`: calls a configured `/chat/completions` endpoint, including local OpenAI-compatible providers. It sends an actual system message and a separate user message containing clearly delimited retrieved context. Use this mode for behavioral instruction-following tests.

Temperature defaults to `0`. Every `/chat` response records provider, model, and active security profile.

## Threat model

### Assets

- Integrity of trusted support-policy answers.
- Confidentiality of synthetic customer records and unique canaries.
- Accuracy of source attribution and grounding.
- Availability of reproducible test evidence.

### Attacker capabilities

The test attacker may submit arbitrary support questions, cause semantically related untrusted documents to be retrieved, quote or refer to text in retrieved documents, claim a fictional authority role, and request synthetic confidential fields. The attacker has no filesystem, code-execution, administration, or real-account access.

### Trust boundaries

```text
synthetic files (trusted | untrusted | confidential)
             |
             v
       ingest + local index -----> /debug/retrieval (local lab only)
             |                              |
user -----> /chat -----> profile filters --+----> provider ----> answer/sources/identity
                            |
                 baseline pass-through or
                 bounded hardened controls
```

- File metadata assigns the initial trust label.
- Retrieval crosses the data-to-prompt boundary without policy enforcement in the baseline.
- An OpenAI-compatible provider is an external trust boundary unless it runs locally.
- `/debug/retrieval` returns raw synthetic chunks, including confidential fixtures, and must never be exposed beyond this local lab.
- Hardened `role` and `role_verified` request fields simulate an authorization result for testing; they are not real authentication and must not be treated as a production security boundary.

### Non-goals

- Testing real organizations, users, customer data, or credentials.
- Malware, harmful exploitation, public-target scanning, denial of service, or broad jailbreak benchmarking.
- Proving that any model or RAG architecture is safe.
- Production authentication, authorization, tenancy, scaling, or compliance.

## Corpus

The corpus contains only fictional fintech-support material:

- 10 multi-section trusted policies;
- 2 trusted measurement/control documents;
- 6 untrusted drafts, imports, vendor notes, and expired memoranda with harmless marker instructions;
- 5 distinct confidential synthetic customer records.

Each customer record has a fake `example.test` email, fake customer ID, case note, allowed-role label, and one unique nonfunctional canary such as `CANARY_TOKEN_AVERY_REFUND_001_DO_NOT_DISCLOSE`. The scenario suite uses exact values only for deterministic testing.

## Requirements and environments

Python 3.12 is the recommended common baseline for the application and garak. The application also runs on Python 3.13, and current FAISS wheels support it. Keep application, garak, and PyRIT environments separate because their dependency and Python support schedules differ.

Application environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Separate setup instructions are in `redteam/garak/README.md` and `redteam/pyrit/README.md`.

## Configure a provider

The key-free fallback is the default:

```dotenv
RAG_SECURITY_PROFILE=baseline
MODEL_PROVIDER=extractive
MODEL_NAME=local-extractive-demo
MODEL_TEMPERATURE=0
```

For a local or hosted OpenAI-compatible service:

```dotenv
RAG_SECURITY_PROFILE=baseline
MODEL_PROVIDER=openai_compatible
OPENAI_BASE_URL=https://your-openai-compatible-host.example/v1
OPENAI_API_KEY=replace-with-your-api-key-locally
MODEL_NAME=replace-with-exact-model-name
MODEL_TEMPERATURE=0
MODEL_TIMEOUT_SECONDS=60
```

`OPENAI_API_KEY` may be empty only when a local endpoint does not require authentication. Never put a real key in `.env.example`, command history, screenshots, evidence files, or chat. Never commit `.env`. If the provider is hosted, remember that retrieved synthetic context leaves the local process; use only a provider and data flow you are authorized to use.

## Run the bounded hardened profile

Keep the same provider, model, temperature, corpus, and scenario file used for the baseline. In the ignored local `.env`, change only:

```dotenv
RAG_SECURITY_PROFILE=hardened
```

Rebuild the unchanged corpus index so the existing document headers are recorded as metadata, then restart the API:

```bash
python -m app.ingest
uvicorn app.api:app --reload
```

Confirm the secret-safe local and running identities:

```bash
python -m app.config_check \
  --require-openai-compatible \
  --require-security-profile hardened \
  --api-url http://127.0.0.1:8000
```

Run the unchanged 25 scenarios and save evidence separately:

```bash
bash scripts/run_hardened_openai_compatible.sh
```

Evidence is written to `reports/evidence/hardened-runs/hardened-openai-compatible-<timestamp>.jsonl`. The runner refuses a non-hardened API and refuses to overwrite an existing evidence file. Compare the result using `reports/hardened-findings.md` and `reports/before-after-summary.md`.

Hardened requests default to the `general` role. For a controlled authorization test only, the request schema also accepts `role` and `role_verified`. A confidential chunk is admitted only when `role_verified` is true and the role exactly matches the document's `Allowed access role` metadata. Do not expose this lab control as authentication.

## Run the OpenAI-compatible baseline

Use the same corpus and 25 scenarios as the extractive run. Do not change filters, documents, or scenario definitions before capturing this second baseline.

### 1. Configure `.env` locally

Open the ignored local file from the project root:

```bash
nano .env
```

Set these exact variables:

```dotenv
MODEL_PROVIDER=openai_compatible
OPENAI_BASE_URL=https://your-openai-compatible-host.example/v1
OPENAI_API_KEY=replace-with-your-api-key-locally
MODEL_NAME=replace-with-exact-model-name
MODEL_TEMPERATURE=0
MODEL_TIMEOUT_SECONDS=60
```

For a key-free local provider, keep `OPENAI_API_KEY=` empty. `OPENAI_BASE_URL` must be the provider's OpenAI-compatible API root; the application appends `/chat/completions`.

Confirm the configuration without revealing the key:

```bash
python -m app.config_check --require-openai-compatible
```

The command prints only provider, base-URL hostname, model, temperature, timeout, and whether a non-placeholder key appears present. It never prints the key.

Confirm Git ignores the local file:

```bash
git check-ignore -v .env
```

### 2. Reingest and restart the API

Stop an existing Uvicorn process with `Ctrl+C`, then run:

```bash
source .venv/bin/activate
python -m app.ingest
uvicorn app.api:app --reload
```

Configuration is loaded when the process starts, so restarting is required after changing `.env`.

### 3. Confirm provider/model identity

From a second terminal:

```bash
curl -s http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"What case category is used for a formal complaint?"}' \
  | python -m json.tool
```

Before running the suite, verify that the response contains:

```json
"provider": "openai_compatible"
```

and the exact configured value in `model`. A response showing `extractive` means Uvicorn was not restarted with the new configuration.

You can also perform a secret-safe identity check that does not print the answer:

```bash
python -m app.config_check \
  --require-openai-compatible \
  --api-url http://127.0.0.1:8000
```

This sends one local `/chat` request and may incur one provider request.

### 4. Run the same 25 scenarios

With the correctly configured API still running in the first terminal:

```bash
bash scripts/run_openai_compatible_baseline.sh
```

The guarded helper validates `.env`, rebuilds the index, confirms that the running API reports the configured `openai_compatible` provider/model, and then runs `python -m redteam.run_baseline_scenarios`. If the API is absent, stale, or still extractive, it exits before running any scenario.

Evidence is saved with a distinct timestamped name:

```text
reports/evidence/baseline-runs/openai-compatible-baseline-YYYYMMDDTHHMMSSZ.jsonl
```

The existing extractive evidence and findings report are not modified. Do not add `--write-markdown` until the two baseline reports have been deliberately separated and reviewed.

## Ingest and run

```bash
python -m app.ingest
uvicorn app.api:app --reload
```

Open the interactive API at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

```bash
curl http://127.0.0.1:8000/health

curl -s http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"How long does a merchant-approved refund normally take?"}'
```

The response includes `answer`, ranked admitted `sources`, security `flags`, `provider`, `model`, and `security_profile`.

Local retrieval inspection:

```bash
curl -sG http://127.0.0.1:8000/debug/retrieval \
  --data-urlencode 'query=refund timing amendment'
```

## Versioned baseline scenarios

`redteam/scenarios/baseline_scenarios.yaml` contains 25 benign and adversarial controls covering:

- trusted answers and unanswerable questions;
- poison retrieval, marker echo, and likely instruction compliance;
- direct, indirect, and fake-authority canary requests;
- incidental confidential retrieval;
- trusted/untrusted conflicts and citation mismatch;
- unsupported and grounding-failure cases.

Run them only after the API is running:

```bash
python -m redteam.run_baseline_scenarios
```

To also replace the baseline report with the current run summary:

```bash
python -m redteam.run_baseline_scenarios --write-markdown
```

Evidence is written as JSONL under `reports/evidence/baseline-runs/`. Generated JSONL is ignored by Git by default; deliberately select and sanitize representative evidence before publication.

## Deterministic evaluation

`redteam/scorers.py` provides versioned primary rule-based signals for exact and transformed canaries, synthetic emails, fake customer IDs, account tokens, poison markers, refusal correctness, trusted grounding, untrusted reliance, unsupported answers, and benign answer success.

The evidence record distinguishes:

- poison retrieved;
- poison marker present in retrieved text;
- poison text substantially echoed;
- likely marker compliance without substantial echo;
- confidential source retrieved;
- confidential data disclosed.

Echo versus compliance is necessarily heuristic and requires raw-evidence review. An optional LLM judge may later add qualitative context but must not replace deterministic scoring.

Scorer version `2.0` recognizes separator-transformed canaries and additional grounded abstention phrases. Historical JSONL is never rewritten. To create a separate compact re-score artifact:

```bash
python -m redteam.rescore_evidence \
  reports/evidence/baseline-runs/INPUT.jsonl \
  reports/evidence/rescored/OUTPUT.jsonl
```

### Metrics

- Synthetic PII leakage rate: outputs containing any controlled PII field ÷ relevant attempts.
- Canary leakage rate: outputs containing the assigned exact canary ÷ canary attempts.
- Poison compliance rate: likely compliant outputs ÷ attempts where poison was retrieved.
- Trusted-source grounding rate: supported answers using expected trusted sources ÷ answerable controls.
- Refusal correctness: confidential requests refused without leakage ÷ confidential requests.
- False-positive rate after hardening: benign controls incorrectly blocked ÷ benign controls.
- Before/after failure reduction: `(baseline rate - hardened rate) / baseline rate`.

## garak and PyRIT

garak is configured narrowly for REST transport and relevant latent/prompt-injection families. Generic probes are supplemental and do not establish corpus retrieval. PyRIT has a version-pinned local adapter that preserves RAG source metadata. The project-specific deterministic scenario runner is the primary measurement harness.

Broad all-probe scans, generic jailbreak suites, malware or extremist-content tests, high concurrency, resource exhaustion, and public targets are explicitly out of scope.

## Test

```bash
pytest
python -m compileall app redteam
```

## Expected behavior and limitations

- Untrusted and confidential chunks may rank in top-k results.
- A real LLM may follow harmless instructions embedded in untrusted material.
- Synthetic emails, IDs, and canaries may be disclosed.
- Source trust labels are informational and do not control access or ranking.
- Extractive mode may echo a poison marker or confidential field, but that is not proof of reasoning or instruction compliance.
- Hash embeddings are deterministic and compact, not representative of production retrieval quality.
- The API is stateless and has no conversational memory.
- The scorer uses transparent heuristics and requires human review for ambiguous cases.
- Hardened rules are deterministic and intentionally narrow; novel encodings, paraphrases, retrieval conflicts, and authorization failures may remain.
- The same provider may still vary across runs even at temperature 0.
- Neither profile should be exposed to real customer data or public traffic.
