#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "build/app.bin" ]; then
    echo "Check failed: build/app.bin missing" >&2
    exit 1
fi

if [ ! -s "build/app.bin" ]; then
    echo "Check failed: build/app.bin is empty" >&2
    exit 1
fi

if [ ! -f "build/result.txt" ] || ! grep -q "BUILD_SUCCESS" "build/result.txt"; then
    echo "Check failed: build/result.txt missing or invalid" >&2
    exit 1
fi

echo "Check passed: multistep build targets verified."
exit 0
