# Arena Memory Reclamation
Heavyweight subtasks execute in isolated child processes using fork and waitpid.
Resource management follows operating system arena isolation principles:
- The orchestrator process maintains a minimal supervisory context footprint.
- Forked child processes receive isolated memory spaces and ephemeral directories.
- Shell traps on EXIT signal ensure temporary scratch directories unmount cleanly.
- Worker outcomes serialize to bounded disk artifacts before process termination.
Terminating child processes releases all resident memory allocations to the OS.
Process boundaries act as arena garbage collectors preventing context growth.
Parent orchestrators monitor child completion via waitpid return status.