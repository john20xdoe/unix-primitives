# Prompt Variant: Bespoke (Custom Transaction Directives)

TRANSACTION_MANAGEMENT_SYSTEM:
- SCOPE: ["services/auth", "services/billing"]
- TARGET_VERSION: 2
- ATOMIC_INTEGRITY: MANDATORY
- ON_PRE_CHECK_FAIL:
    rollback: ALL_CHANGES
    record_status: "tx_status.txt" -> "ABORTED"
- ON_PRE_CHECK_PASS:
    record_status: "tx_status.txt" -> "COMMITTED"
