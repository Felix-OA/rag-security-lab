# Before/After Summary

This comparison uses three OpenAI-compatible baseline replications and three hardened OpenAI-compatible replications. Each side produced internally stable signal and scenario-label results. The corpus, 25 scenarios, provider, model, and temperature were unchanged. A reduction in these controlled signals is evidence about this lab configuration only.

## Primary Comparison

| Metric | OpenAI-Compatible Baseline (each of 3) | Hardened (each of 3) | Change |
|---|---:|---:|---:|
| Scenarios | 25 | 25 | 0 |
| Passed | 14 (56%) | 14 (56%) | 0 |
| Failed | 11 (44%) | 11 (44%) | 0 |
| Raw untrusted retrieval exposures | 15 | 15 | 0 |
| Untrusted contexts admitted to model | 15 | 0 | -15 |
| Untrusted source reliance | 0–1 | 0 | Reduced to zero in all hardened runs |
| Raw confidential retrieval exposures | 7 | 7 | 0 |
| Confidential contexts admitted to model | 7 | 0 | -7 |
| Confidential-context exclusions | 0 | 7 | +7 enforced exclusions |
| Reviewed synthetic PII/canary disclosures | 3 | 0 | -3 |
| Exact canary disclosures | 2 | 0 | -2 |
| Transformed canary disclosures | 1 | 0 | -1 |
| Correct confidentiality refusals | 4/7 (57%) | 7/7 (100%) | +3 correct refusals |
| Poison markers present in raw retrieval | 15 | 15 | 0 |
| Poison marker echoes | 0 | 0 | No change |
| Likely instruction compliance | 0 observed | 0 observed | No change |
| Confirmed grounding failures | 0* | 0** | No confirmed change |
| Trusted-source grounding signal | 11 | 10 | -1 |
| Benign-answer success signal | 4 | 3 | -1 |
| Output-redaction activations | Not active | 0 | Not exercised by any hardened run |

\* Each baseline run had one automated grounding flag that manual review classified as a correct abstention.

\** Every hardened run had the same three automated grounding flags. Manual review classified all three as correct abstentions and scorer false positives.

## Hardened Replication Stability

| Metric | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| Passed / failed | 14 / 11 | 14 / 11 | 14 / 11 |
| Reviewed PII/canary disclosures | 0 | 0 | 0 |
| Correct confidentiality refusals | 7/7 | 7/7 | 7/7 |
| Confidential contexts admitted | 0 | 0 | 0 |
| Untrusted contexts admitted | 0 | 0 | 0 |
| Poison-marker echoes | 0 | 0 | 0 |
| Likely instruction compliance | 0 | 0 | 0 |
| Confirmed grounding failures | 0 | 0 | 0 |
| Scorer false positives | 3 | 3 | 3 |
| Utility/source-coverage failures | 2 | 2 | 2 |

All three runs had identical scenario labels, post-filter source selections, flags, and measured security signals. Response wording varied in 12 scenarios and latency varied, without changing these outcomes.

## What Improved

- **Confidentiality boundary:** Seven raw confidential retrievals still occurred, but zero confidential chunks were admitted to model context. All seven direct or indirect confidentiality scenarios received correct refusals.
- **Answer leakage:** The recurring baseline pattern of two exact plus one transformed synthetic canary disclosure fell to zero. This is answer-level improvement, not a claim that raw retrieval exposure disappeared.
- **Source trust enforcement:** Fifteen instruction-like untrusted chunks were detected and excluded before generation in every hardened run. None recorded untrusted-source reliance.
- **Poison-content containment:** Raw retrieval still contained poison markers in 15 scenarios, but those marker-bearing contexts were excluded and marker echo remained at zero.

## What Did Not Improve

- **Raw retrieval exposure:** The unchanged vector search continued to retrieve untrusted chunks in 15 scenarios and confidential chunks in 7.
- **Top-line pass rate:** The result remained 14/25 because eliminated leakage failures were replaced by utility, source-expectation, and scorer failures.
- **Answer availability:** Filtering sometimes removed relevant material without refilling the context window from eligible trusted sources. Two scenarios then lacked enough trusted context for the expected answer.
- **Grounding/utility signals:** Trusted-source grounding decreased from 11 to 10 and benign-answer success from 4 to 3.
- **Output-redaction evidence:** No output-redaction flag fired in any hardened run, so the replications did not show whether redaction would catch a leak that passed the earlier controls.
- **General injection assurance:** Zero observed marker compliance covers only the fixed safe fixtures. It does not demonstrate prompt-injection prevention or resistance to novel/adaptive attacks.

## Failure Interpretation

The unchanged 11-failure total is not evidence that hardening had no effect. The baseline failures included three recurring reviewed canary disclosures and incomplete confidentiality refusals. Those did not recur in any hardened replication. The stable hardened failures instead included:

- three confirmed unknown-answer scorer false positives;
- several rigid required-phrase or expected-source mismatches despite safe answers;
- two meaningful cases where filtering left insufficient trusted context to answer usefully.

No hardened failure contained a reviewed synthetic canary disclosure, poison-marker echo, untrusted-source reliance, or confirmed invented phone number, address, or exchange rate.

## PyRIT/Custom Baseline vs Hardened

Both runs used PyRIT 0.14.0 through the same local `pyrit-http-adapter`, the same 25 scenarios, and the same provider/model/temperature. The baseline evidence is `pyrit-custom-baseline-20260719T111054Z.jsonl`; the hardened evidence is `pyrit-custom-hardened-20260720T131446Z.jsonl`.

| Metric | PyRIT/Custom Baseline | PyRIT/Custom Hardened | Change |
|---|---:|---:|---:|
| Passed / failed | 14 / 11 | 14 / 11 | No change |
| Reviewed PII/canary disclosures | 3 | 0 | -3 |
| Exact / transformed canary disclosures | 2 / 1 | 0 / 0 | Reduced to zero |
| Correct confidentiality refusals | 4/7 | 7/7 | +3 |
| Raw confidential retrievals | 7 | 7 | No change |
| Confidential contexts admitted | 7 | 0 | -7 |
| Raw untrusted retrievals | 15 | 15 | No change |
| Untrusted contexts admitted | 15 | 0 | -15 |
| Untrusted-source reliance | 1 | 0 | -1 heuristic signal |
| Poison-marker echoes | 1 | 0 | -1 |
| Likely instruction compliance | 0 observed | 0 observed | No change |
| Confirmed grounding failures | 0 | 0 | No change |
| Scorer false positives | 1 | 3 | +2 |
| Utility/source-coverage failures | Not separately reported | 2 | Two hardened availability misses |
| Trusted-source grounding signal | 11 | 10 | -1 |
| Benign-answer success signal | 4 | 3 | -1 |

### Interpretation

- **Improved:** Bounded hardening reduced observed leakage and context admission in this synthetic local lab. Reviewed canary disclosure fell from three to zero, confidentiality refusal correctness rose from 4/7 to 7/7, and no confidential or untrusted raw retrieval was admitted to model context.
- **Stayed the same:** Raw retrieval exposure remained seven confidential and 15 untrusted scenarios. The top-line pass/fail result remained 14/11, and neither run showed marker-defined instruction compliance or a confirmed grounding failure.
- **Improved poison containment:** The one baseline poison-marker echo did not recur. That baseline event was content echo while rejecting the poisoned rule, not instruction compliance.
- **Got worse:** Automated scorer false positives increased from one to three, while trusted-grounding and benign-answer signals each declined by one.
- **Utility tradeoff:** Excluding disallowed chunks without refilling the context window left two hardened scenarios without the relevant trusted source. Safe abstention or incomplete answers replaced the expected useful policy response.
- **Measurement limit:** The adapter preserves retrieval and response evidence but does not provide broad PyRIT orchestration, adaptive attacks, an LLM judge, or general security assurance. Historical baseline and hardened scorer versions also differ.

## garak Narrow Baseline vs Hardened

Bounded garak probes were used as supporting evidence in this local synthetic lab. Both runs used garak 0.15.1, the same two harmless tier-1 latent-injection snippet probes, six attempts per probe, one generation, disabled parallelism, and the local `/chat` request shape.

| Metric | garak narrow baseline | garak narrow hardened | Change |
|---|---:|---:|---:|
| Attempts | 12 | 12 | 0 |
| Trigger emitted | 7 | 4 | -3 |
| Trigger absent | 5 | 8 | +3 |
| Detector attack-success rate | 58.3% | 33.3% | -25 percentage points |
| Eiffel trigger emissions | 3/6 | 2/6 | -1 |
| Legal trigger emissions | 4/6 | 2/6 | -2 |

### Interpretation

- **Changed:** Trigger emission decreased from seven to four attempts, with fewer emissions for both probes.
- **Remained:** Both probe types still emitted a trigger under the hardened profile. Direct-prompt latent-injection behavior was reduced in this run, not eliminated.
- **Control attribution:** Hardened prompt and context behavior may have influenced the result, but one low-volume run cannot establish causality. Hosted-model variation remains a plausible contributor.
- **Not RAG poisoning proof:** garak supplied the injection text directly as the user’s question. It did not seed a document, verify poisoned retrieval, call `/debug/retrieval`, or record source metadata and application flags.
- **Measurement limit:** A trigger match records string emission, not whether the model complied with a retrieved instruction or trusted an untrusted source. These results supplement rather than replace the custom RAG and PyRIT/custom evidence.

## Measurement Boundaries

- **Retrieval exposure** is raw top-k material returned by `/debug/retrieval`.
- **Context admission/exclusion** is whether that material appears in `/chat` sources and is passed to the model.
- **Answer disclosure** is controlled synthetic content reaching the response.
- **Output redaction** is a post-generation fallback and should be credited only when its flags show an actual redaction.
- **Refusal correctness** applies only when refusing is appropriate for a confidentiality-seeking scenario.
- **Source trust enforcement** means excluding or deprioritizing untrusted context; merely retrieving it does not equal reliance.
- **Content echo** is not automatically instruction compliance.
- **Prompt-injection resistance** cannot be established from zero marker emissions in 25 fixed scenarios.

## Next Stage

The planned baseline-versus-hardened evidence set is now complete: replicated custom scenarios, PyRIT/custom comparison, and bounded garak supporting evidence. The project is ready to draft a public case study, provided the final narrative preserves the measurement boundaries, distinguishes direct prompts from retrieved poisoning, and avoids security, compliance, certification, or production-readiness claims.

> These findings do not establish secure RAG, prompt-injection prevention, compliance, general model safety, or production readiness.
