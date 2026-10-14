#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "services/auth/config.json" ] || [ ! -f "services/billing/config.json" ]; then
    echo "Verification error: service configs missing" >&2
    exit 1
fi

V_AUTH=$(grep -o '"version"[[:space:]]*:[[:space:]]*[0-9]*' services/auth/config.json | awk -F: '{print $2}' | tr -d ' ')
V_BILL=$(grep -o '"version"[[:space:]]*:[[:space:]]*[0-9]*' services/billing/config.json | awk -F: '{print $2}' | tr -d ' ')

if [ "$V_AUTH" != "$V_BILL" ]; then
    echo "Verification error: schema version inconsistency (auth: $V_AUTH, billing: $V_BILL)" >&2
    exit 1
fi

echo "Services consistent at version $V_AUTH"
exit 0
