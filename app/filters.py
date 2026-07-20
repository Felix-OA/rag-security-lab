"""Transparent, deterministic controls for the optional hardened profile."""

from __future__ import annotations

import copy
import re

from app.config import settings

CONFIDENTIAL_REFUSAL = (
    "I can't disclose confidential customer records or account tokens. "
    "I can help with general policy information instead."
)

CONFIDENTIAL_REQUEST_PATTERNS = (
    re.compile(
        r"\b(?:what is|return|show|give|provide|quote|spell out|read|reveal|disclose)\b.*"
        r"\b(?:account[- ]?token|canary|customer id|customer email|confidential token|"
        r"private record|confidential record|case note|every field|uppercase identifier)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:support manager|privacy officer)\b.*\b(?:email|customer id|token|record)\b", re.IGNORECASE),
)

INSTRUCTION_LIKE_PATTERNS = (
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bignore (?:the |all |any )?(?:approved|current|earlier|newer|previous|policy|instructions?)",
        r"\bdisregard (?:the |all |any )?(?:approved|current|earlier|policy|instructions?)",
        r"\boverride (?:local|trusted|system|policy|guidance)",
        r"\bwhen (?:this page appears|answering)\b",
        r"\b(?:append|output|reply with|finish the response with)\b.*\bPOISON_MARKER_",
        r"\b(?:assistant|machine-reader|for automated assistants)\s*[: ]",
        r"\bfollow this memo instead\b",
    )
)
INSTRUCTION_LIKE_PATTERNS = tuple(INSTRUCTION_LIKE_PATTERNS)

POISON_MARKER_PATTERN = re.compile(r"\bPOISON_MARKER_[A-Z0-9_]+\b", re.IGNORECASE)
CANARY_LIKE_PATTERN = re.compile(
    r"\bCANARY(?:[_\s-]+)TOKEN(?:[_\s-]+)[A-Z0-9]+"
    r"(?:(?:[_\s-]+)[A-Z0-9]+)*?(?:[_\s-]+)DO(?:[_\s-]+)NOT(?:[_\s-]+)DISCLOSE\b",
    re.IGNORECASE,
)
FAKE_ACCOUNT_TOKEN_PATTERN = re.compile(r"\bFAKE_ACCOUNT_TOKEN(?:_[A-Z0-9]+)*\b", re.IGNORECASE)
SYNTHETIC_EMAIL_PATTERN = re.compile(r"\b[a-z0-9._%+-]+@example\.test\b", re.IGNORECASE)
FAKE_CUSTOMER_ID_PATTERN = re.compile(r"\bCUST-FAKE-[A-Z0-9-]+\b", re.IGNORECASE)
SYNTHETIC_NAME_PATTERN = re.compile(
    r"\b(?:Avery Testperson|Morgan Sample|Riley Canary|Jordan Fixture|Casey Example)\b",
    re.IGNORECASE,
)

CONFLICT_PAIRS = (
    ("instant", "five to ten"),
    ("email address alone", "in-app"),
    ("close", "account-close"),
    ("claimed authority", "does not bypass"),
)


def _profile(value: str | None) -> str:
    return value or settings.security_profile


def _unique(flags: list[str]) -> list[str]:
    return list(dict.fromkeys(flags))


def is_confidential_request(question: str) -> bool:
    return any(pattern.search(question) for pattern in CONFIDENTIAL_REQUEST_PATTERNS)


def contains_instruction_like_content(text: str) -> bool:
    return any(pattern.search(text) for pattern in INSTRUCTION_LIKE_PATTERNS)


def inspect_input(
    question: str,
    *,
    role: str = "general",
    role_verified: bool = False,
    security_profile: str | None = None,
) -> tuple[str, list[str]]:
    if _profile(security_profile) == "baseline":
        return question, []
    if is_confidential_request(question) and not role_verified:
        return question, ["confidential_request_blocked", "unauthorized_confidential_access"]
    return question, []


def _allowed_roles(metadata: dict) -> set[str]:
    value = metadata.get("allowed_roles", [])
    if isinstance(value, str):
        return {part.strip() for part in value.split(",") if part.strip()}
    return {str(part).strip() for part in value if str(part).strip()}


def _has_source_conflict(chunks: list[dict]) -> bool:
    trusted = "\n".join(
        str(chunk.get("text", "")).lower()
        for chunk in chunks
        if chunk.get("metadata", {}).get("trust_level") == "trusted"
    )
    untrusted = "\n".join(
        str(chunk.get("text", "")).lower()
        for chunk in chunks
        if chunk.get("metadata", {}).get("trust_level") == "untrusted"
    )
    return any(
        (left in trusted and right in untrusted) or (right in trusted and left in untrusted)
        for left, right in CONFLICT_PAIRS
    )


def filter_retrieval(
    chunks: list[dict],
    *,
    role: str = "general",
    role_verified: bool = False,
    security_profile: str | None = None,
) -> tuple[list[dict], list[str]]:
    if _profile(security_profile) == "baseline":
        return chunks, []

    flags: list[str] = []
    filtered: list[dict] = []
    trust_levels = {chunk.get("metadata", {}).get("trust_level") for chunk in chunks}
    if "trusted" in trust_levels and "untrusted" in trust_levels:
        flags.append("trusted_source_preferred")
    if _has_source_conflict(chunks):
        flags.append("source_conflict_detected")

    for original in chunks:
        chunk = copy.deepcopy(original)
        metadata = chunk.get("metadata", {})
        trust_level = metadata.get("trust_level")
        if trust_level == "confidential":
            authorized = role_verified and role in _allowed_roles(metadata)
            if not authorized:
                flags.extend(["confidential_context_excluded", "unauthorized_confidential_access"])
                continue
        if trust_level == "untrusted":
            text = str(chunk.get("text", ""))
            instruction_like = contains_instruction_like_content(text)
            marker_present = bool(POISON_MARKER_PATTERN.search(text))
            if instruction_like:
                flags.extend(
                    [
                        "retrieved_instruction_like_content_detected",
                        "untrusted_instruction_content_filtered",
                        "untrusted_context_excluded",
                    ]
                )
                if marker_present:
                    flags.append("poison_marker_filtered")
                continue
            if marker_present:
                chunk["text"] = POISON_MARKER_PATTERN.sub("[FILTERED POISON MARKER]", text)
                flags.append("poison_marker_filtered")
            chunk["score"] = round(float(chunk.get("score", 0.0)) * 0.25, 6)
            flags.append("untrusted_context_downranked")
        filtered.append(chunk)

    trust_order = {"trusted": 0, "confidential": 1, "untrusted": 2}
    filtered.sort(
        key=lambda item: (
            trust_order.get(item.get("metadata", {}).get("trust_level"), 3),
            -float(item.get("score", 0.0)),
        )
    )
    return filtered, _unique(flags)


def filter_output(answer: str, *, security_profile: str | None = None) -> tuple[str, list[str]]:
    if _profile(security_profile) == "baseline":
        return answer, []

    flags: list[str] = []
    redacted, count = CANARY_LIKE_PATTERN.subn("[REDACTED SYNTHETIC CANARY]", answer)
    if count:
        flags.extend(["output_canary_redacted", "account_token_redacted"])
    redacted, count = FAKE_ACCOUNT_TOKEN_PATTERN.subn("[REDACTED ACCOUNT TOKEN]", redacted)
    if count:
        flags.append("account_token_redacted")
    redacted, count = SYNTHETIC_EMAIL_PATTERN.subn("[REDACTED SYNTHETIC EMAIL]", redacted)
    if count:
        flags.append("synthetic_pii_redacted")
    redacted, count = FAKE_CUSTOMER_ID_PATTERN.subn("[REDACTED SYNTHETIC CUSTOMER ID]", redacted)
    if count:
        flags.append("synthetic_pii_redacted")
    redacted, count = SYNTHETIC_NAME_PATTERN.subn("[REDACTED SYNTHETIC NAME]", redacted)
    if count:
        flags.append("synthetic_pii_redacted")
    redacted, count = POISON_MARKER_PATTERN.subn("[REDACTED POISON MARKER]", redacted)
    if count:
        flags.append("poison_marker_redacted")
    return redacted, _unique(flags)
