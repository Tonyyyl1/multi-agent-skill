#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PY="${REPO_ROOT}/install.py"
SKILL_SOURCE="${REPO_ROOT}/skills/apex-commander"
TARGET_DIR="${HOME}/.gemini/config/skills/apex-commander"

if command -v python3 >/dev/null 2>&1; then
  python3 "${INSTALL_PY}" "$@"
else
  mkdir -p "$(dirname "${TARGET_DIR}")"
  rm -rf "${TARGET_DIR}"
  cp -R "${SKILL_SOURCE}" "${TARGET_DIR}"
  chmod +x "${TARGET_DIR}/scripts/install_mac.sh" || true
  echo "[OK] Installed apex-commander to: ${TARGET_DIR} (POSIX fallback)"
fi
