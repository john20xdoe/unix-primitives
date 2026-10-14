#!/usr/bin/env bash
set -euo pipefail
echo "call" >> .calls
echo "Sync error: connection refused by upstream replica" >&2
exit 1
