#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.gemini/config/skills"
MODE="${1:---symlink}"

echo "=== Installing Unix-Primitives Suite ==="
echo "Source: ${SCRIPT_DIR}/skills"
echo "Target: ${TARGET_DIR}"
echo "Mode:   ${MODE}"

mkdir -p "${TARGET_DIR}"

for skill_path in "${SCRIPT_DIR}/skills"/*; do
    if [ -d "${skill_path}" ]; then
        skill_name="$(basename "${skill_path}")"
        dest="${TARGET_DIR}/${skill_name}"
        
        # Remove existing destination if it exists
        rm -rf "${dest}"
        
        if [ "${MODE}" = "--copy" ]; then
            cp -R "${skill_path}" "${dest}"
            echo "  [copied] ${skill_name} -> ${dest}"
        else
            ln -sfn "${skill_path}" "${dest}"
            echo "  [linked] ${skill_name} -> ${dest} (live sync)"
        fi
    fi
done

echo ""
echo "Installation complete. The following slash commands are active:"
echo "  /unix-init"
echo "  /unix-stamp"
echo "  /unix-status"
echo "  /unix-clean"
echo "  /unix-hook"
echo "  /unix-primitives"
