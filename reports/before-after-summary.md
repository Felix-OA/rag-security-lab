# Before/After Summary

This comparison uses the stable result from each of three OpenAI-compatible baseline replications and the first hardened OpenAI-compatible run. The corpus, 25 scenarios, provider, model, and temperature were unchanged. A reduction in these controlled signals is evidence about this lab configuration only.

## Primary Comparison

| Metric | OpenAI-Compatible Baseline | Hardened | Change |
|---|---:|---:|---:|
| Scenarios | 25 | 25 | 0 |
| Passed | 14 (56%) | 14 (56%) | 0 |
| Failed | 11 (44%) | 11 (44%) | 0 |
| Raw untrusted retrieval exposures | 15 | 15 | 0 |
| Untrusted contexts admitted to model | 15 | 0 | -15 |
| Untrusted source reliance | 0–1 | 0 | Reduced to zero in this run |
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
| Output-redaction activations | Not active | 0 | Not exercised by this run |

\* Each baseline run had one automated grounding flag that manual review classified as a correct abstention.

\** The hardened run had three automated grounding flags. Manual review classified all three as correct abstentions and scorer false positives.

## What Improved

- **Confidentiality boundary:** Seven raw confidential retrievals still occurred, but zero confidential chunks were admitted to model context. All seven direct or indirect confidentiality scenarios received correct refusals.
- **Answer leakage:** The recurring baseline pattern of two exact plus one transformed synthetic canary disclosure fell to zero. This is answer-level improvement, not a claim that raw retrieval exposure disappeared.
- **Source trust enforcement:** Fifteen instruction-like untrusted chunks were detected and excluded before generation. The hardened run recorded no untrusted-source reliance.
- **Poison-content containment:** Raw retrieval still contained poison markers in 15 scenarios, but those marker-bearing contexts were excluded and marker echo remained at zero.

## What Did Not Improve

- **Raw retrieval exposure:** The unchanged vector search continued to retrieve untrusted chunks in 15 scenarios and confidential chunks in 7.
- **Top-line pass rate:** The result remained 14/25 because eliminated leakage failures were replaced by utility, source-expectation, and scorer failures.
- **Answer availability:** Filtering sometimes removed relevant material without refilling the context window from eligible trusted sources. Two scenarios then lacked enough trusted context for the expected answer.
- **Grounding/utility signals:** Trusted-source grounding decreased from 11 to 10 and benign-answer success from 4 to 3.
- **Output-redaction evidence:** No output-redaction flag fired, so the run did not show whether redaction would catch a leak that passed the earlier controls.
- **General injection assurance:** Zero observed marker compliance covers only the fixed safe fixtures. It does not demonstrate prompt-injection prevention or resistance to novel/adaptive attacks.

## Failure Interpretation

The unchanged 11-failure total is not evidence that hardening had no effect. The baseline failures included three recurring reviewed canary disclosures and incomplete confidentiality refusals. Those did not recur. The hardened failures instead included:

- three confirmed unknown-answer scorer false positives;
- several rigid required-phrase or expected-source mismatches despite safe answers;
- two meaningful cases where filtering left insufficient trusted context to answer usefully.

No hardened failure contained a reviewed synthetic canary disclosure, poison-marker echo, untrusted-source reliance, or confirmed invented phone number, address, or exchange rate.

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

1. Run the hardened PyRIT/custom adapter against the same 25 scenarios first. It captures raw retrieval and answer evidence, so the before/after boundary measurements remain comparable.
2. Run the bounded hardened garak probes afterward as a separate direct-prompt test. Do not treat trigger emission or non-emission as retrieval-poisoning evidence without retrieval capture.
3. Before publishing a final case study, replicate the hardened suite for consistency and complete both tool retests. A draft case study can be prepared now, but the final public claim set should include those results and preserve the limitations above.

> These findings do not establish secure RAG, prompt-injection prevention, compliance, general model safety, or production readiness.
