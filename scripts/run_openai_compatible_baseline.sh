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

echo "Using Python: ${PYTHON_BIN}"
echo "Validating secret-safe OpenAI-compatible configuration..."
"${PYTHON_BIN}" -m app.config_check --require-openai-compatible

echo "Rebuilding the unchanged synthetic corpus index..."
"${PYTHON_BIN}" -m app.ingest

echo "Checking the running API identity at ${API_URL}..."
if ! "${PYTHON_BIN}" -m app.config_check --require-openai-compatible --api-url "${API_URL}"; then
  echo
  echo "The API is not ready with the configured provider/model."
  echo "In another terminal, activate the app environment and run:"
  echo "  uvicorn app.api:app --reload"
  echo "Then rerun this script. No scenarios were executed."
  exit 2
fi

RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_PATH="reports/evidence/baseline-runs/openai-compatible-baseline-${RUN_STAMP}.jsonl"

echo "Running the same versioned 25-scenario baseline suite..."
"${PYTHON_BIN}" -m redteam.run_baseline_scenarios \
  --base-url "${API_URL}" \
  --output "${OUTPUT_PATH}"

echo "OpenAI-compatible baseline evidence saved to: ${OUTPUT_PATH}"
echo "The existing extractive evidence was not modified."
