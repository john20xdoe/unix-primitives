#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.gemini/config/skills"

MODE="--symlink"
FORCE=0

for arg in "$@"; do
    case "$arg" in
        --symlink)
            MODE="--symlink"
            ;;
        --copy)
            MODE="--copy"
            ;;
        --force)
            FORCE=1
            ;;
        -h|--help)
            echo "Usage: $0 [--symlink|--copy] [--force]"
            exit 0
            ;;
        *)
            echo "Error: Unknown argument '$arg'" >&2
            echo "Usage: $0 [--symlink|--copy] [--force]" >&2
            exit 2
            ;;
    esac
done

echo "=== Installing Unix-Primitives Suite ==="
echo "Source: ${SCRIPT_DIR}/skills"
echo "Target: ${TARGET_DIR}"
echo "Mode:   ${MODE}"

mkdir -p "${TARGET_DIR}"

installed_skills=()

for skill_path in "${SCRIPT_DIR}/skills"/*; do
    if [ -d "${skill_path}" ]; then
        skill_name="$(basename "${skill_path}")"
        dest="${TARGET_DIR}/${skill_name}"
        
        if [ -L "${dest}" ]; then
            link_target="$(readlink "${dest}" || true)"
            case "${link_target}" in
                "${SCRIPT_DIR}"*|*"skills/${skill_name}"*)
                    rm -f "${dest}"
                    ;;
                *)
                    if [ "${FORCE}" -eq 1 ]; then
                        mv "${dest}" "${dest}.bak.$(date +%s)"
                    else
                        echo "Warning: ${dest} is symlink to external target; skipping (use --force to overwrite)" >&2
                        continue
                    fi
                    ;;
            esac
        elif [ -e "${dest}" ]; then
            if [ "${FORCE}" -eq 1 ]; then
                mv "${dest}" "${dest}.bak.$(date +%s)"
            else
                echo "Warning: ${dest} exists and is not managed symlink; skipping (use --force to overwrite)" >&2
                continue
            fi
        fi

        if [ "${MODE}" = "--copy" ]; then
            cp -R "${skill_path}" "${dest}"
            echo "  [copied] ${skill_name} -> ${dest}"
        else
            ln -sfn "${skill_path}" "${dest}"
            echo "  [linked] ${skill_name} -> ${dest} (live sync)"
        fi
        installed_skills+=("/${skill_name}")
    fi
done

echo ""
echo "Installation complete. The following slash commands are active:"
for cmd in "${installed_skills[@]}"; do
    echo "  ${cmd}"
done
