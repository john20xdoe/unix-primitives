# Standard Stream Demultiplexing
System output separates strictly across standard POSIX stream file descriptors.
Channel demultiplexing follows standard operating system conventions:
- File descriptor 1 (stdout) streams machine-readable payloads exclusively.
- File descriptor 2 (stderr) receives human diagnostics, telemetry, and progress.
- Exit status communicates execution success or failure via integer return codes.
Consumers redirect file descriptor 1 directly into automated downstream parsers.
Diagnostic logging on file descriptor 2 does not contaminate data parsing.
Tools parsing standard output receive clean AST, diff, or serialized payloads.
Channel segregation eliminates conversational text from machine pipelines.