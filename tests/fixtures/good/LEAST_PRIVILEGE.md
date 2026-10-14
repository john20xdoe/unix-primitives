# Security Capability Boundaries
Worker subagents operate under hardware and sandbox capability restrictions.
Process execution environments enforce POSIX security capabilities:
- Read access is granted via CAP_READ_FS across designated repository trees.
- Mutation capabilities including CAP_WRITE_FS are stripped at initialization.
- Shell execution permissions CAP_EXEC_SHELL are permanently revoked.
System call monitors enforce capability masks at the kernel interface.
Unauthorized file mutation attempts raise EPERM exceptions automatically.
Security boundaries rely on operating system sandbox rules rather than prompts.
Worker processes inherit immutable credential boundaries from parent supervisors.