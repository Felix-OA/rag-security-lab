"""Security filter extension points (inactive in the vulnerable baseline)."""

from __future__ import annotations


def inspect_input(question: str) -> tuple[str, list[str]]:
    # TODO(hardening): detect input risk and adversarial query patterns.
    return question, []


def filter_retrieval(chunks: list[dict]) -> tuple[list[dict], list[str]]:
    # TODO(hardening): filter or isolate untrusted and confidential retrievals.
    return chunks, []


def filter_output(answer: str) -> tuple[str, list[str]]:
    # TODO(hardening): redact synthetic PII before returning output.
    # TODO(hardening): detect fake canary leakage and raise a security flag.
    return answer, []
