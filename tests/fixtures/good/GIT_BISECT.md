# Causal Fault Localization
Defect isolation follows a logarithmic search algorithm across version history.
The diagnostic search coordinates through the following protocol:
- Identify known good and known bad commit boundaries across the repository dag.
- Probe the topological midpoint between the known boundaries.
- Execute automated verification commands at the selected commit probe.
- Narrow the search window by half based on verification exit codes.
Convergence completes in ceiling log base two of N probe iterations.
Linear commit scanning is avoided in favor of binary partitioning.
The bisecting runner outputs the exact first defective commit hash.
The resulting commit identifier feeds into patch reversal workflows.