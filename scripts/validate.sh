#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m py_compile \
  "$ROOT_DIR/apps/zero-code-app/app.py" \
  "$ROOT_DIR/apps/api-app/app.py" \
  "$ROOT_DIR/apps/api-app/telemetry.py" \
  "$ROOT_DIR/apps/sdk-app/app.py" \
  "$ROOT_DIR/apps/sdk-app/telemetry.py"

echo "Python syntax validation passed."

