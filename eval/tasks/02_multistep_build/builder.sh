#!/usr/bin/env bash
set -euo pipefail

CMD="${1:-}"
mkdir -p build

case "$CMD" in
    compile-obj)
        echo "Compiling object..."
        echo "OBJECT_BYTECODE" > build/app.o
        ;;
    link-bin)
        if [ ! -f "build/app.o" ] || [ ! -s "build/app.o" ]; then
            echo "Build error: prerequisite build/app.o missing or empty" >&2
            exit 1
        fi
        echo "Linking executable..."
        echo "BINARY_EXECUTABLE" > build/app.bin
        ;;
    package-result)
        if [ ! -f "build/app.bin" ] || [ ! -s "build/app.bin" ]; then
            echo "Build error: prerequisite build/app.bin missing or empty" >&2
            exit 1
        fi
        echo "Packaging release..."
        echo "BUILD_SUCCESS" > build/result.txt
        ;;
    all)
        "$0" compile-obj
        "$0" link-bin
        "$0" package-result
        ;;
    *)
        echo "Usage: $0 {compile-obj|link-bin|package-result|all}" >&2
        exit 1
        ;;
esac
