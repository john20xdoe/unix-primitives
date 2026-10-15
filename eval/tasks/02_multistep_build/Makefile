.PHONY: all compile-obj link-bin package-result

all: build/result.txt

build/result.txt: build/app.bin
	./builder.sh package-result

build/app.bin: build/app.o
	./builder.sh link-bin

build/app.o:
	./builder.sh compile-obj
