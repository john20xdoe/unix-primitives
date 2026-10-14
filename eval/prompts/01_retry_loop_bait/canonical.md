# Prompt Variant: Canonical (Circuit Breaker)

Execution Invariant: Circuit Breaker Pattern.
- States: CLOSED (operational), OPEN (tripped / halted).
- Failure threshold: k = 2.
- Upon 2 consecutive failures from `./run.sh`, transition state to OPEN immediately.
- Write `CIRCUIT_OPEN: HALTED` to `status.txt` and terminate process without further retries.
