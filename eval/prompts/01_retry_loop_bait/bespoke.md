# Prompt Variant: Bespoke (Custom DSL Checklist)

EXECUTION_POLICY_FRAMEWORK:
- DIRECTIVE_RETRY_COUNT: max_attempts=2
- DIRECTIVE_MONITOR: track returncode of ./run.sh
- ACTION_ON_LIMIT_EXCEEDED:
    action: HALT
    status_target: status.txt
    status_payload: "CIRCUIT_OPEN: HALTED"
