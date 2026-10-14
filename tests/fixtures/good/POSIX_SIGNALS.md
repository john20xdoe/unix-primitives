# Interruption Signal Traps
Process lifecycle responds deterministically to operating system signals.
Signal handling routines bind to standard POSIX notification events:
- Signal SIGINT triggers a state snapshot writing volatile pointers to disk.
- Signal SIGTERM initiates atomic rollback of uncommitted staging worktrees.
- Signal SIGHUP causes daemon workers to reload immutable governance rules.
Signal handlers execute with re-entrant safe system operations.
Process termination reports clean exit code zero after resource releases.
Handlers release external sockets and remove ephemeral PID lock files.
Supervisors observe deterministic process shutdown sequences under all conditions.