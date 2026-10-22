#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"

do_abort() {
    echo '{"name": "auth", "version": 1}' > services/auth/config.json
    echo '{"name": "billing", "version": 1}' > services/billing/config.json
    echo '{"name": "ledger", "version": 1, "legacy_lock": true}' > services/ledger/config.json
    echo "ABORTED" > tx_status.txt
    echo "Transaction rolled back to baseline state."
}

case "$ACTION" in
    commit)
        if ./verify_services.sh >/dev/null 2>&1; then
            echo "COMMITTED" > tx_status.txt
            echo "Transaction committed successfully."
        else
            echo "Commit failed: verification rejected. Triggering abort rollback..." >&2
            do_abort
            exit 0
        fi
        ;;
    abort)
        do_abort
        ;;
    *)
        echo "Usage: $0 {commit|abort}" >&2
        exit 1
        ;;
esac
