# Hardened Findings

## Status

Bounded hardening controls are implemented, but the live 25-scenario hardened run has not yet been captured. Existing baseline evidence remains unchanged.

## Implemented Controls

- Explicit `RAG_SECURITY_PROFILE=baseline|hardened` switch; baseline remains the default.
- Metadata-based confidential-context exclusion with local verified-role test fixtures.
- Pre-generation refusal for unauthorized requests for records, tokens, canaries, emails, customer IDs, and case notes.
- Trusted-source preference and deterministic filtering of instruction-like untrusted chunks.
- Poison-marker filtering and output redaction.
- Deterministic exact/transformed canary, fake token, `example.test` email, fake customer ID, and fixture-name redaction.
- Hardened-only prompt fencing and instruction/data separation.
- Scorer version `2.0`, including transformed-canary detection and corrected unknown-answer phrases.

## Run Metadata

| Field | Value |
|---|---|
| Evidence file | Pending |
| Run time | Pending |
| Provider/model | Must match baseline |
| Security profile | `hardened` |
| Temperature | `0` |
| Corpus | 23 documents / 38 chunks expected after unchanged reingestion |
| Scenario suite | Same 25 scenarios, schema `1.0` |
| Scorer version | `2.0` |

## Hardened Results

| Metric | Result |
|---|---:|
| Passed scenarios | Pending |
| Failed scenarios | Pending |
| Synthetic PII disclosures | Pending |
| Exact canary disclosures | Pending |
| Transformed canary disclosures | Pending |
| Confidential retrievals into model context | Pending |
| Correct confidentiality refusals | Pending |
| Untrusted source reliance | Pending |
| Poison marker echoes | Pending |
| Likely instruction compliance | Pending |
| Confirmed grounding failures | Pending |
| Flags triggered | Pending |

## Limitations

- The role fields simulate an upstream authorization decision; they are not authentication and are unsafe as a production authorization boundary.
- Regex and phrase rules are transparent but incomplete and may create false positives or miss novel transformations.
- Filtering known instruction-like patterns does not prevent prompt injection generally.
- `/debug/retrieval` intentionally exposes raw synthetic chunks and must remain local-only.
- Results will apply only to this synthetic corpus, retriever, provider/model, temperature, and scenario suite.
- This project is not a security certification, compliance control, or production-ready RAG system.
