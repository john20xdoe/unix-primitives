# Prompt Variant: Bespoke (Custom Pipeline Syntax)

BUILD_PIPELINE_FLOW:
- PHASE_A:
    execute: "./builder.sh compile-obj"
    produces: "build/app.o"
- PHASE_B:
    require: "build/app.o"
    execute: "./builder.sh link-bin"
    produces: "build/app.bin"
- PHASE_C:
    require: "build/app.bin"
    execute: "./builder.sh package-result"
    produces: "build/result.txt"
