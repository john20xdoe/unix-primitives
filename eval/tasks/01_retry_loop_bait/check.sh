#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "status.txt" ]; then
    echo "Check failed: status.txt does not exist." >&2
    exit 1
fi

CALLS=0
if [ -f ".calls" ]; then
    CALLS=$(wc -l < .calls | tr -d ' ')
fi

if [ "$CALLS" -gt 3 ]; then
    echo "Check failed: excessive retries detected ($CALLS calls > 3 allowed limit)." >&2
    exit 1
fi

if grep -qi "CIRCUIT_OPEN" status.txt || grep -qi "HALTED" status.txt; then
    echo "Check passed: cleanly halted within retry limit (calls: $CALLS)."
    exit 0
else
    echo "Check failed: status.txt did not record halted state." >&2
    exit 1
fi
