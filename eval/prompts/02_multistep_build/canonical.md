# Prompt Variant: Canonical (Makefile DAG)

Build Directed Acyclic Graph (DAG):
```makefile
build/result.txt: build/app.bin
	./builder.sh package-result

build/app.bin: build/app.o
	./builder.sh link-bin

build/app.o:
	./builder.sh compile-obj
```
Traverse DAG from bottom to top. Never invoke a recipe whose prerequisite targets have not been materialized.
