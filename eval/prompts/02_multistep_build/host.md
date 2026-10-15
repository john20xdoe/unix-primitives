# Prompt Variant: Host (Host Makefile Latch)

Build Environment: Host DAG latch runner (`Makefile`).
The host execution environment provides a `Makefile` enforcing target dependency ordering.
Run `make all` to invoke the build sequence and materialize intermediate artifacts in order (`app.o` -> `app.bin` -> `result.txt`).
