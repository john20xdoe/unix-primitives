# Shell Execution Environment
All automation scripts execute with strict error propagation enabled.
The execution runtime initializes with standard posix shell safety flags:
- Option -e forces immediate process exit upon non-zero command return.
- Option -u treats expansion of unpopulated environment variables as fatal.
- Option -o pipefail preserves non-zero exit codes across pipeline segments.
Subshells inherit these environment invariants unconditionally.
Default error code propagation ensures no transient commands fail quietly.
Scripts terminate deterministically at the exact line encountering defects.
Diagnostic exit codes surface directly to caller supervisors.