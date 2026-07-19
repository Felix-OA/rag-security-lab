"""Print a secret-safe summary of local provider configuration."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlsplit

from app.config import Settings, settings


def safe_config_summary(config: Settings) -> dict[str, Any]:
    parsed = urlsplit(config.api_base_url)
    key_value = config.api_key.strip()
    key_present = bool(key_value) and "replace-with" not in key_value.lower()
    return {
        "provider": config.model_provider,
        "base_url_host": parsed.hostname or "invalid-or-missing",
        "model": config.model_name,
        "temperature": config.model_temperature,
        "timeout_seconds": config.request_timeout,
        "api_key_present": key_present,
    }


def validate_openai_compatible(config: Settings) -> None:
    if config.model_provider != "openai_compatible":
        raise ValueError("MODEL_PROVIDER is not set to openai_compatible")
    parsed = urlsplit(config.api_base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("OPENAI_BASE_URL must be an absolute http(s) URL")
    if not config.model_name or "replace-with" in config.model_name.lower() or config.model_name == "your-model-name":
        raise ValueError("MODEL_NAME must identify the exact configured model")
    if config.model_temperature != 0:
        raise ValueError("MODEL_TEMPERATURE must be 0 for the comparable baseline run")


def check_running_api(api_url: str, config: Settings) -> dict[str, str]:
    body = json.dumps({"question": "What case category is used for a formal complaint?"}).encode("utf-8")
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.request_timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not validate the running local API: {exc}") from exc
    identity = {"provider": str(payload.get("provider", "unknown")), "model": str(payload.get("model", "unknown"))}
    if identity != {"provider": config.model_provider, "model": config.model_name}:
        raise RuntimeError(
            "Running API identity does not match .env; restart uvicorn after changing provider configuration"
        )
    return identity


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-openai-compatible", action="store_true")
    parser.add_argument("--api-url", help="Optionally verify provider/model through one local /chat request")
    args = parser.parse_args()

    if args.require_openai_compatible:
        validate_openai_compatible(settings)
    summary = safe_config_summary(settings)
    for key, value in summary.items():
        print(f"{key}: {str(value).lower() if isinstance(value, bool) else value}")
    if settings.model_provider == "openai_compatible" and not summary["api_key_present"]:
        print("api_key_note: absent; valid only if the configured local endpoint requires no key")
    if args.api_url:
        identity = check_running_api(args.api_url, settings)
        print(f"running_api_provider: {identity['provider']}")
        print(f"running_api_model: {identity['model']}")
        print("running_api_identity_matches_env: true")


if __name__ == "__main__":
    main()
