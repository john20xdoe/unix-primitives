# Subagent Delegation Protocol (Primitive #3: Process Control & Arena GC)

For deep semantic audits of directory workspaces (e.g. `.agents/`) or complex multi-file prompt rulesets, orchestrators delegate classification to an isolated read-only child subagent.

## Protocol Steps

### Step 1: Generate Full Non-Paraphrased Payload
Run `audit-prompt` to build the complete, unparaphrased subagent instruction bundle:

```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py audit-prompt "<target>"
```

This bundle provides exact target inventory, CLI scan telemetry, the dynamically generated 7 OS Subsystems / 17 Primitives classification contract, and pointer to `references/rosetta_stone.md`—giving the subagent 100% of the operational data needed for scan without token bloat or guessing.

### Step 2: Spawn Child Subagent
Invoke child subagent via `invoke_subagent`:
* `TypeName`: `research` (or `self`)
* `Role`: `Prompt Architecture Auditor`
* `Prompt`: Generated unparaphrased payload from Step 1.

### Step 3: Child Execution & Artifact Flushing
Child reads target files, classifies each into the 7 OS Subsystems or Domain Reference, writes markdown findings to disk (`.state/artifacts/prompt_audit.md` via `state_manager.py artifact`), and exits.

```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py artifact --role "audit" --content - << 'EOF'
# Audit Findings
...
EOF
```

### Step 4: Orchestrator Memory Preservation
Child virtual memory is discarded upon completion. Parent orchestrator retains clean working context and surfaces the audit report to the user.
