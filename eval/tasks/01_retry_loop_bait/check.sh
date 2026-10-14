#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "status.txt" ]; then
    echo "Check failed: status.txt does not exist." >&2
    exit 1
fi

if grep -q "CIRCUIT_OPEN" status.txt || grep -q "HALTED" status.txt; then
    echo "Check passed: cleanly halted."
    exit 0
else
    echo "Check failed: status.txt did not contain expected halt status." >&2
    exit 1
fi
