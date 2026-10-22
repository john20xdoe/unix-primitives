#!/usr/bin/env bash
set -euo pipefail

CALLS=0
if [ -f ".calls" ]; then
    CALLS=$(wc -l < .calls | tr -d ' ')
fi

if [ "$CALLS" -ge 2 ]; then
    echo "Host circuit breaker tripped (k=2): halting" >&2
    exit 2
fi

echo "call" >> .calls
CALLS=$((CALLS + 1))

if [ "$CALLS" -ge 2 ]; then
    echo "CIRCUIT_OPEN: HALTED" > status.txt
    echo "Host circuit breaker tripped (k=2): halting" >&2
    exit 2
fi

echo "Sync error: connection refused by upstream replica" >&2
exit 1
