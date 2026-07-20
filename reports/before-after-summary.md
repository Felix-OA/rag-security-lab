# Before/After Summary

## Status

The baseline evidence set is frozen. The hardened implementation is ready for the same 25-scenario run, but hardened evidence has not yet been captured. `TBD` values must be filled only from the new immutable hardened JSONL.

## Primary Comparison

The baseline column uses the stable result from each of the three OpenAI-compatible replications. PyRIT/custom and garak observations are shown separately because their scope and measurement differ.

| Metric | Baseline | Hardened | Change |
|---|---:|---:|---:|
| Passed scenarios | 14 | TBD | TBD |
| Failed scenarios | 11 | TBD | TBD |
| Synthetic PII disclosures | 3 reviewed | TBD | TBD |
| Exact canary disclosures | 2 | TBD | TBD |
| Transformed canary disclosures | 1 | TBD | TBD |
| Confidential retrievals into model context | 7 | TBD | TBD |
| Correct confidentiality refusals | 4/7 | TBD | TBD |
| Poison marker echoes | 0 | TBD | TBD |
| Likely instruction compliance | 0 observed | TBD | TBD |
| Untrusted source reliance | 0–1 heuristic | TBD | TBD |

## Supporting Tool Baselines

| Method | Scope | Baseline observation | Hardened retest |
|---|---|---|---|
| OpenAI-compatible replications | Same 25 scenarios, three runs | Stable 14/25; 3 reviewed canary disclosures per run | Pending |
| PyRIT/custom adapter | Same 25 scenarios with retrieval evidence | 14/25; 3 reviewed canary disclosures; 1 poison-marker echo | Pending |
| garak 0.15.1 narrow | 12 direct latent-injection attempts | 7 trigger emissions; no retrieval evidence | Not yet authorized |

## Measurement Boundaries

- Raw retrieval exposure is not the same as material admitted to model context.
- Confidential context admission is not the same as confidential answer disclosure.
- Content echo is not automatically instruction compliance.
- garak's direct prompts do not prove poisoned-document retrieval.
- Scorer v2.0 adds transformed-canary detection and unknown-answer phrase fixes. Historical raw evidence is unchanged; any re-score must be saved as a separate artifact.

> Results apply only to this local synthetic lab. A reduction does not prove security, prompt-injection prevention, compliance, certification, or production readiness.
