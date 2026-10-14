# Quality Assurance Pipeline
Static analysis executes across several discrete compiler passes.
Diagnostic messages follow structured compiler emission conventions:
- Each diagnostic reports an identifier of the form error[SCAR-XX].
- The report specifies exact source coordinate as file, line, and column.
- Severity levels are constrained to BLKR, WARN, or NIT classifications.
- The breached invariant is cited directly from architectural contracts.
- A concrete unified patch diff illustrates the required resolution.
Peer praise and conversational commentary are strictly omitted.
Automated linters enforce zero warnings prior to merge.