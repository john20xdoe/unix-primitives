#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "build/app.o" ] || [ ! -s "build/app.o" ]; then
    echo "Check failed: build/app.o missing or empty" >&2
    exit 1
fi

if [ ! -f "build/app.bin" ] || [ ! -s "build/app.bin" ]; then
    echo "Check failed: build/app.bin missing or empty" >&2
    exit 1
fi

if [ ! -f "build/result.txt" ] || ! grep -q "BUILD_SUCCESS" "build/result.txt"; then
    echo "Check failed: build/result.txt missing or invalid" >&2
    exit 1
fi

# Verify chronological dependency order via mtime
if [ "build/app.o" -nt "build/app.bin" ]; then
    echo "Check failed: build/app.o is newer than build/app.bin (out of order)" >&2
    exit 1
fi

if [ "build/app.bin" -nt "build/result.txt" ]; then
    echo "Check failed: build/app.bin is newer than build/result.txt (out of order)" >&2
    exit 1
fi

echo "Check passed: multistep build targets verified."
exit 0
