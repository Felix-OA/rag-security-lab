#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="${PYTHON_BIN}"
elif [[ -x "${PROJECT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
else
  PYTHON_BIN="python"
fi
API_URL="${RAG_LAB_API_URL:-http://127.0.0.1:8000}"

echo "Validating secret-safe hardened OpenAI-compatible configuration..."
"${PYTHON_BIN}" -m app.config_check \
  --require-openai-compatible \
  --require-security-profile hardened

echo "Rebuilding the unchanged synthetic corpus index with document metadata..."
"${PYTHON_BIN}" -m app.ingest

echo "Checking the running hardened API identity at ${API_URL}..."
"${PYTHON_BIN}" -m app.config_check \
  --require-openai-compatible \
  --require-security-profile hardened \
  --api-url "${API_URL}"

echo "Running the unchanged versioned 25-scenario suite in hardened mode..."
"${PYTHON_BIN}" -m redteam.run_hardened_scenarios --base-url "${API_URL}"

echo "Existing baseline evidence was not modified."
