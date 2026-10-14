# Fault Tolerance Policy
Subsystem execution implements a finite state machine for recovery.
The executor operates under a threshold of k=2 consecutive execution errors.
State transitions follow deterministic boundaries:
- CLOSED: commands execute normally and reset the consecutive error count.
- OPEN: on the second consecutive error, state trips immediately to halt.
Further execution attempts are suppressed without repetition.
The executor flushes diagnostic telemetry to the supervisor channel.
A human landing engineer must inspect the failure cause before reset.
State reverts to HALF-OPEN only upon human landing intervention.