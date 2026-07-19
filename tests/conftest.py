"""Keep the unit-test process isolated from developer machine model settings."""

from __future__ import annotations

import os


# This file is imported by pytest before test modules import ``app.config``.
# Environment values take precedence over python-dotenv's non-overriding load, so
# tests cannot inherit an OpenAI-compatible provider or make a paid model request.
os.environ["MODEL_PROVIDER"] = "extractive"
os.environ["MODEL_NAME"] = "local-extractive-demo"
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:9/v1"
os.environ["MODEL_TEMPERATURE"] = "0"
