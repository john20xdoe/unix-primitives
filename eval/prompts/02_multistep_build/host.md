# Prompt Variant: Host (Host Makefile Latch)

Build Environment: Host DAG latch runner.
The host execution runner invokes the target chain via Makefile dependencies.
Each step validates file timestamps (`app.o` <= `app.bin` <= `result.txt`).
Run the build sequence ensuring all intermediate artifacts are produced in order.
