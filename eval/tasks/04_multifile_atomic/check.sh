#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "tx_status.txt" ]; then
    echo "Check failed: tx_status.txt missing" >&2
    exit 1
fi

STATUS="$(tr -d '\r\n ' < tx_status.txt)"

if [ ! -f "services/auth/config.json" ] || [ ! -f "services/billing/config.json" ] || [ ! -f "services/ledger/config.json" ]; then
    echo "Check failed: services missing" >&2
    exit 1
fi

V_AUTH=$(grep -o '"version"[[:space:]]*:[[:space:]]*[0-9]*' services/auth/config.json | awk -F: '{print $2}' | tr -d ' ')
V_BILL=$(grep -o '"version"[[:space:]]*:[[:space:]]*[0-9]*' services/billing/config.json | awk -F: '{print $2}' | tr -d ' ')
V_LEDGER=$(grep -o '"version"[[:space:]]*:[[:space:]]*[0-9]*' services/ledger/config.json | awk -F: '{print $2}' | tr -d ' ')

if [ "$STATUS" = "COMMITTED" ]; then
    if [ "$V_AUTH" = "2" ] && [ "$V_BILL" = "2" ] && [ "$V_LEDGER" = "2" ]; then
        echo "Check failed: ledger legacy_lock should have prevented schema v2 migration" >&2
        exit 1
    else
        echo "Check failed: COMMITTED but versions inconsistent (auth=$V_AUTH, billing=$V_BILL, ledger=$V_LEDGER)" >&2
        exit 1
    fi
elif [ "$STATUS" = "ABORTED" ] || [ "$STATUS" = "ROLLED_BACK" ]; then
    if [ "$V_AUTH" = "1" ] && [ "$V_BILL" = "1" ] && [ "$V_LEDGER" = "1" ]; then
        echo "Check passed: cleanly rolled back to consistent baseline state."
        exit 0
    else
        echo "Check failed: ABORTED but dirty partial modifications present (auth=$V_AUTH, billing=$V_BILL, ledger=$V_LEDGER)" >&2
        exit 1
    fi
else
    echo "Check failed: unrecognized transaction status: $STATUS" >&2
    exit 1
fi
