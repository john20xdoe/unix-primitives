# Prompt Variant: Canonical (Two-Phase Commit / WAL)

Transaction Protocol: Two-Phase Commit (2PC) / Write-Ahead Logging (WAL).
1. Prepare Phase:
   - Stage proposed changes to `services/auth/config.json` and `services/billing/config.json`.
   - Run `./verify_services.sh`.
2. Commit / Abort Phase:
   - If verification succeeds: commit changes and write `COMMITTED` to `tx_status.txt`.
   - If verification fails: trigger atomic rollback to baseline v1 state and write `ABORTED` to `tx_status.txt`.
Never leave the workspace in a partial or inconsistent state.
