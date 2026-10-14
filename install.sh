#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${UNIX_PRIMITIVES_TARGET:-${HOME}/.gemini/config/skills}"

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
            managed_target="${SCRIPT_DIR}/skills/${skill_name}"
            if command -v realpath >/dev/null 2>&1; then
                resolved_link="$(realpath "${dest}" 2>/dev/null || true)"
                resolved_managed="$(realpath "${managed_target}" 2>/dev/null || true)"
            else
                resolved_link="${link_target}"
                resolved_managed="${managed_target}"
            fi

            if [ "${link_target}" = "${managed_target}" ] || [ -n "${resolved_managed}" -a "${resolved_link}" = "${resolved_managed}" ]; then
                rm -f "${dest}"
            else
                if [ "${FORCE}" -eq 1 ]; then
                    mv "${dest}" "${dest}.bak.$(date +%s)"
                else
                    echo "Warning: ${dest} is symlink to external target; skipping (use --force to overwrite)" >&2
                    continue
                fi
            fi
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
