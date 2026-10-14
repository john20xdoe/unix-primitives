# Prompt Variant: Host (Host WAL / Transaction Supervisor)

Host Environment: Transaction WAL Guard.
- File modifications in services/ are monitored by the host transaction engine.
- Atomic commit is only released if `./verify_services.sh` succeeds.
- If pre-commit conditions fail, host supervisor restores snapshot and writes ABORTED to `tx_status.txt`.
- When valid, host finalizes update and writes COMMITTED to `tx_status.txt`.
