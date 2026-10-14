# Concurrent Resource Coordination
Worker processes coordinate disk access through posix advisory file locks.
Mutations against shared files follow deterministic synchronization protocols:
- A dedicated lock file with a dot-lock extension is acquired before access.
- System call flock with exclusive flag LOCK_EX coordinates contention.
- Lock acquisition enforces a bounded timeout before timeout escalation.
- File descriptors holding locks are flushed and closed upon task completion.
Advisory locking prevents interleaved disk mutations across parallel workers.
Lock acquisition and release cycles are recorded in auditing streams.
Deadlock avoidance protocols enforce alphabetical ordering on multiple locks.