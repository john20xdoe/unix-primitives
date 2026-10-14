# System Formalisms

## Execution Invariants
- Circuit Breaker: On error, threshold k=2. If repeated failure >= 2, transition state to OPEN, write CIRCUIT_OPEN to status, and halt.
- Build DAG: Backward-chaining target verification (result.txt <- app.bin).
- Least Privilege: Read-only access on protected resources. Mutating protected.txt violates system contract.
