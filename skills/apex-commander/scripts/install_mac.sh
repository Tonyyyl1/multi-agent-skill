#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SOURCE="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${HOME}/.gemini/config/skills/apex-commander"

if command -v python3 >/dev/null 2>&1; then
  python3 "${SCRIPT_DIR}/install_global.py" "$@"
else
  mkdir -p "$(dirname "${TARGET_DIR}")"
  rm -rf "${TARGET_DIR}"
  cp -R "${SKILL_SOURCE}" "${TARGET_DIR}"
  chmod +x "${TARGET_DIR}/scripts/install_mac.sh" || true
  echo "[OK] Installed apex-commander globally to: ${TARGET_DIR} (POSIX fallback)"
fi
