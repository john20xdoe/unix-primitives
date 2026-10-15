# Prompt Variant: Host (Host WAL / Transaction Supervisor)

Host Environment: Transaction WAL Guard (`./transaction.sh`).
- File modifications in `services/` are guarded by the host transaction engine.
- Update `services/auth/config.json` and `services/billing/config.json` to version 2.
- Execute `./transaction.sh commit` to verify and atomically finalize the transaction.
- If verification fails or upgrade is incomplete, invoke `./transaction.sh abort` to roll back to baseline.
