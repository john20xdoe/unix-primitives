---
name: unix-primitives
description: >
  Refactor, convert, or generate system prompts, agent skills, cursorrules, CLAUDE.md,
  workflows, and README guidelines into canonical Unix & computer science primitives (Makefile DAGs,
  /etc/init.d runlevel latches, RFC 822 headers, RFC 5234 EBNF, Design-by-Contract,
  Circuit Breakers, 2PC/WAL, git bisect, LKML patch series, compiler diagnostics).
  Eliminates fragile English checklists and zero-frequency prompt DSLs by leveraging 50 years
  of pre-training weight gravity.
  Trigger: /unix-primitives [scan|convert|rewrite|generate] [target], "convert prompt to unix primitives",
  "apply pre-training gravity", "unix prompt converter", "refactor prompt to unix". Defaults to 'scan' when command omitted.
---

# Unix Primitives (Pre-Training Gravity Skill)

## Purpose

Transforms fragile natural-language prompts, numbered checklists, and zero-frequency prompt DSLs (`Freq ≈ 0`) into canonical Unix and computer science formalisms (`Freq > 1,000,000`).

> [!IMPORTANT]
> **Resolution Invariant (Zero Search Token Burn)**:
> This skill is installed globally at `~/.gemini/config/skills/unix-primitives/SKILL.md`.
> When invoked in any workspace containing a local `.agents/` folder:
> * **DO NOT** execute exploratory tool calls searching `.agents/skills/unix-primitives` if absent.
> * Immediately load and execute via the canonical global installation: `~/.gemini/config/skills/unix-primitives/`.
> * Run `python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py link-agents` to auto-link skills into `.agents/skills/` if local registration is desired.

---

## Triggers & Usage

* `/unix-primitives [filepath | .agents-folder]` (or bare `/unix-primitives`): **Default behavior (scan)**. Audits prompt file or workspace for friction. If target is omitted, auto-detects local `.agents/`, `CLAUDE.md`, `.cursorrules`, or `README.md`.
* `/unix-primitives scan <filepath | .agents-folder>`: Explicit friction audit. (Restricted to local workspaces; rejects global paths).
* `/unix-primitives delta <original> <rewritten>`: Compute friction score delta, percentage reduction, and resolved primitives.
* `/unix-primitives convert <filepath>`: Non-destructive conversion. Writes refactored output to `<filepath>.NN.md` (e.g. `CLAUDE.01.md`), leaving original untouched.
* `/unix-primitives rewrite <filepath>`: In-place rewrite. Saves backup to `<filepath>_original` (e.g. `.md_original` to prevent duplicate prompt discovery) and updates original file.
* `/unix-primitives generate <task description>`: Generate brand-new skill, prompt, workflow, or ruleset architected entirely with canonical formalisms.


* `/unix-primitives init [dir] [--ticket ID]`: Physically provision bounded `.state/` directory in repo with real Makefile and runlevel latches.
* `/unix-stamp <plan|tdd|impl> "<summary>"`: Write physical milestone latch to disk with named aliases.
* `/unix-status [dir]`: Check active runlevels, disk timestamps, and staleness health.
* `/unix-clean [dir]`: Archive completed ticket and purge transient slots (guarantees zero bloat).
* `/unix-hook [install|remove] [--type pre-push]`: Optional git hook (allows local commits freely; checks milestones only on `git push`).
* Natural language trigger: *"Convert this prompt to unix primitives"*, *"Apply pre-training gravity to this skill"*, *"Initialize unix state in this repo"*.

---

## Canonical CS & Unix Mapping Rules (17 Primitives)

| # | Fragile Prompt Prose (`Freq ≈ 0`) | Canonical CS/Unix Primitive (`Freq > 1,000,000`) | Target Formalism |
|---|-----------------------------------|---------------------------------------------------|------------------|
| 1 | Numbered checklists, `IF/ELSE/GOTO Step X` | **GNU Makefile DAG** | `.PHONY`, `target: prerequisites`, mtime artifact invalidation |
| 2 | Mutable `PROGRESS.md`, in-context todo tracking | **SysV `/etc/init.d` Runlevels + RFC 822** | `00_` to `99_` lexical file latches, `Key: Value` state headers |
| 3 | Verbose subagent delegation, *"clean up temp files"* | **Unix Process Control** | `fork()`, `waitpid()`, `trap ... EXIT`, arena garbage collection |
| 4 | Formatting begging, premature "Certainly!" promises | **RFC 5234 EBNF & Session Types** | Production rules with XOR gate exclusion + Flores negotiation (?Assert before ?Promise) |
| 5 | *"Make sure you test edge cases and error handling"* | **Design-by-Contract + QuickCheck** | `@requires`, `@ensures`, `@invariant`, Hoare triples, algebraic laws |
| 6 | *"Don't leave the repo broken across multiple files"* | **Database WAL + Two-Phase Commit (2PC)** | `BEGIN` $\rightarrow$ `PREPARE` $\rightarrow$ verify all $\rightarrow$ `COMMIT` / `ROLLBACK` |
| 7 | *"Try a couple times; if stuck, stop and ask me"* | **Circuit Breaker FSM + Idempotency Keys** | `k=2` threshold, `CLOSED` $\rightarrow$ `OPEN` trip, immediate hard halt |
| 8 | Linear exploration, *"figure out why this test fails"* | **`git bisect` Binary Partitioning** | `mid = (lo + hi) // 2`, $O(\log_2 N)$ search space halving |
| 9 | *"Break your work into clean, logical commits"* | **LKML `[PATCH 0/N]` Series** | Topological commit DAG, `git rebase --exec "make test"` invariant |
| 10| Polite, superficial review (*"Looks good to me!"*) | **Multi-Pass Compiler Diagnostics** | `error[SCAR-XX]: BLKR/WARN/NIT` with source locations & AST passes |
| 11| Mixed data payload & chat comments | **Stream Demux (`stdout` vs `stderr`)** | FD 1 (payload) vs FD 2 (diagnostics), exit code |
| 12| Unstructured cancel/stop handling | **POSIX Signals (`SIGINT`, `SIGTERM`, `SIGHUP`)** | Traps for state checkpointing and clean rollback |
| 13| Subagent concurrent write collisions | **Advisory File Locking (`flock(2)` / `.lock`)** | Atomic lock acquisition & release on shared files |
| 14| Permissive silent command failures | **Fail-Fast Shell (`set -euo pipefail`)** | Zero-tolerance error bubbling |
| 15| In-place risky speculative trial edits | **Copy-On-Write Scratch Worktrees** | Ephemeral `git worktree` scratch sandboxing |
| 16| Pleading with agent not to touch files | **Least Privilege & Capabilities (`chmod r--`)** | Structural read-only capability enforcement |
| 17| Context window flooding from long logs | **Ring Buffers & FIFO (`logrotate`)** | Constant token ceiling $O(1)$ on log tailing |

---

## Execution Protocol

### Mode 0: Default Scan Audit (`/unix-primitives [target]` or `/unix-primitives scan`)

When invoked without a subcommand (e.g. `/unix-primitives` or `/unix-primitives <target>`) or explicitly via `scan`:
1. **Default Action is ALWAYS `scan`**: Do NOT halt execution or query user for a subcommand. Execute the pre-training friction analysis immediately.
2. **Target Resolution**:
   * If target path is supplied (`/unix-primitives <path>`), scan that target:
     ```bash
     python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py scan "<path>"
     ```
   * If target path is omitted (`/unix-primitives`), run auto-detected scan in workspace:
     ```bash
     python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py
     ```
     The engine auto-detects local `.agents/` folder, `CLAUDE.md`, `.cursorrules`, or `README.md`.
   * **Frontmatter & Pipe Invariant**: The scanner automatically ignores YAML frontmatter metadata (`--- ... ---`). For speculative snippet testing, supports direct strings or Unix pipes without inline Python scripting:
     ```bash
     python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py scan --text "<snippet>" --score-only
     # or via pipe:
     echo "<markdown>" | python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py scan - --score-only
     ```
3. **Mandatory First-Turn Report Protocol**:
   The agent MUST ALWAYS deliver the complete scan report in that initial turn—**NEVER** wait for the user to ask follow-up questions:
   * **Pre-Training Friction Audit**: Numeric friction scores, detected anti-patterns, and mapped canonical primitives.
   * **Canonical Architecture Audit (7 OS Subsystems / 17 Primitives)**:
     - *[1/7] Build & Execution DAGs*: GNU Makefile DAG (`MAKEFILE_DAG`) for sequential build/test/lint command pipelines.
     - *[2/7] State Persistence & Lifecycle*: SysV `/etc/init.d` Runlevels + RFC 822 (`SYSV_INITD`) for progress tracking / latches, and POSIX Signals (`POSIX_SIGNALS`) for deterministic interruption traps.
     - *[3/7] Process Isolation & Concurrency*: Unix Process Control (`PROCESS_ISOLATION`), Advisory File Locking (`FILE_LOCKING`), and Least Privilege (`LEAST_PRIVILEGE`).
     - *[4/7] Protocols & Stream Demux*: RFC 5234 EBNF & Session Types (`EBNF_GRAMMAR`) for XOR gate exclusion and Flores turn negotiation (`!Customer` vs `?Performer`), Stream Demux (`STREAM_DEMUX`) for stdout/stderr segregation, and Ring Buffers (`RING_BUFFER`) for $O(1)$ log ceilings.
     - *[5/7] Verification & Diagnostics*: Design-by-Contract (`DESIGN_BY_CONTRACT`) for Hoare pre/post conditions, and Multi-Pass Compiler Diagnostics (`COMPILER_DIAGNOSTICS`) for structured static review passes.
     - *[6/7] Transaction Safety & Fault Tolerance*: Database WAL + 2PC (`TWO_PHASE_COMMIT`) for atomic multi-file edits, Circuit Breaker FSM (`CIRCUIT_BREAKER`) for $k=2$ loop breaking, Fail-Fast Shell (`FAIL_FAST_SHELL`), and COW Scratch Worktrees (`SPECULATIVE_COW`).
     - *[7/7] Search & Commit Topology*: `git bisect` (`GIT_BISECT`) for $O(\log_2 N)$ partitioning, and LKML `[PATCH 0/N]` Series (`LKML_PATCH_SERIES`) for bisectable commit DAGs.
     - *[Domain Reference & Invariants]*: Pure architecture specs, technology stacks, and domain conventions preserved as markdown context.
   * **Actionable Recommendations**: Exact commands to run next (e.g. `/unix-primitives convert <path>`, `/unix-init <ticket> <title>`).

4. **Subagent Delegation Protocol (Primitive #3: Process Control & Arena GC)**:
   For deep semantic audits of directory workspaces (e.g. `.agents/`) or complex multi-file prompt rulesets, orchestrators delegate classification to an isolated read-only child subagent:
   * **Step 1: Generate Full Non-Paraphrased Payload**:
     Run `audit-prompt` to build the complete, unparaphrased subagent instruction bundle:
     ```bash
     python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py audit-prompt "<target>"
     ```
     This bundle provides exact target inventory, CLI scan telemetry, the full 7 OS Subsystems / 17 Primitives classification contract, and pointer to `references/rosetta_stone.md`—giving the subagent 100% of the operational data needed for scan without token bloat or guessing.
   * **Step 2: Spawn Child Subagent**:
     Invoke child subagent via `invoke_subagent`:
     - `TypeName`: `research` (or `self`)
     - `Role`: `Prompt Architecture Auditor`
     - `Prompt`: Generated unparaphrased payload from Step 1.
   * **Step 3: Child Execution & Artifact Flushing**:
     Child reads target files, classifies each into the 7 OS Subsystems or Domain Reference, writes markdown findings to disk (`.state/artifacts/prompt_audit.md` via `state_manager.py artifact`), and exits.
   * **Step 4: Orchestrator Memory Preservation**:
     Child virtual memory is discarded upon completion. Parent orchestrator retains clean working context (<30k tokens) and immediately surfaces the complete **Canonical Architecture Audit** across all 17 formalisms to the user.

---

### Mode 1: Convert / Rewrite Existing File (`/unix-primitives convert | rewrite <path>`)

1. **Scan Target**:
   Run scanner to inspect anti-pattern matches and determine output path:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py convert "<path>"
   ```
2. **Determine Target Destination**:
   * **`convert` (Default — Non-Destructive)**: Generates refactored output in `<path>.NN.md` (e.g. `CLAUDE.01.md`, `README.01.md`). The original file remains untouched.
   * **`rewrite` (In-Place)**: Saves backup to `<path>_original` (e.g. `<path>.md_original` to prevent duplicate prompt discovery) before overwriting `<path>`.
3. **Refactor Invariants**:
   * Replace linear instructions with backward-chaining Makefile targets or explicit FSMs.
   * Replace mutable progress tracking with `/etc/init.d`-style disk latches and RFC 822 headers.
   * Replace vague retry advice with a 6-line Circuit Breaker state machine (`threshold k=2`).
   * Replace "test edge cases" with Hoare contracts (`@requires`, `@ensures`) and QuickCheck laws.
   * Replace prose output demands with strict RFC 5234 EBNF production rules.
4. **Preserve Domain Code & Paths Verbatim**:
   * **NEVER** modify existing file paths, variable names, shell commands, or repo-specific business logic.
   * Only refactor the *control flow, execution invariants, state tracking, and protocol definitions*.
5. **Report Score Delta (`delta`)**:
   Execute the delta comparator to report numeric friction reduction:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py delta "<original-path>" "<rewritten-path>"
   ```
   Outputs exact before/after score, % reduction, resolved primitives, and remaining findings without ad-hoc inline python scripting.


---

### Mode 2: Generate New Prompt / Workflow (`/unix-primitives generate <task>`)

When generating prompts, skills, or workflows from scratch:
1. **Model Workflow as DAG**: Use GNU `Makefile` syntax for all multi-step pipelines.
2. **Define State as Disk Latches**: Use `state/00_governance.md`, `state/10_spec.md`, `state/99_next_action.md` with RFC 822 headers.
3. **Impose Circuit Breakers**: Standardize retry limits using `CLOSED -> OPEN` FSM (`k=2`).
4. **Specify Output with EBNF**: Write RFC 5234 grammars for responses requiring machine parsing or human pause gates.
5. **Anchor Invariants with Contracts**: Frame acceptance criteria as `@requires` / `@ensures` Hoare contracts.

---

### Mode 3: Workspace Disk State Engine (`/unix-primitives init | stamp | clean`)

Physical grounding in repository workspaces:

1. **Initialize Workspace (`/unix-init`)**:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py init --workspace . --ticket <ID> --title "<Task>"
   ```
   * Provisions bounded `.state/` directory with `.gitignore`, `00_governance.md`, `10_ticket.md`, `99_next_action.md`, and real `Makefile`.
2. **Stamp Milestone Latch (`/unix-stamp`)**:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py stamp <plan|tdd|impl> "<Summary>" --next-action "<Next>"
   ```
   * Uses named aliases: `plan` (`20_plan.md`), `tdd` (`30_tdd_red.md`), `impl` (`40_impl_green.md`).
   * Updates physical disk `mtime`, advances runlevel, and rewrites volatile `99_next_action.md` in place.
3. **Subagent Arena Output Isolation**:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py artifact --role "<Role>" --content "<Findings>"
   ```
   * Child worker writes directly to disk (`.state/artifacts/<role>.md`); orchestrator retains clean context (<30k tokens).
4. **Optional Pre-Push Hook (`/unix-hook`)**:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py hook --type pre-push
   ```
   * Allows local commits freely; checks `.state/Makefile` milestone validation only on `git push`.
5. **Compaction Recovery**:
   * After 200k+ context compaction, agent runs `/unix-status`, reads highest existing physical latch, and resumes immediately with zero lost steps.

---

## Anti-Bloat & Anti-Staleness Guarantees

1. **Bounded $O(1)$ Slot Allocation**: Strictly 6 discrete slots (`00_`, `10_`, `20_`, `30_`, `40_`, `99_`). Directory never grows beyond 6 active files ($<50\text{KB}$ total).
2. **In-Place Volatile Overwrites**: `99_next_action.md` is overwritten in place every turn, never appended ($<200\text{ bytes}$).
3. **Repository Cleanliness**: `.state/.gitignore` generated automatically so transient latches never pollute git history, staged commits, or PR diffs.
4. **Archive & Prune (`clean`)**: `/unix-primitives clean` rolls completed ticket latches into a single flat archive (`.state/archive/<ticket>.log`) and purges transient slots.
5. **Staleness Expiry**: `status` checks timestamp age ($>72\text{h}$ flags ticket as STALE; prevents executing expired context).

---

## Canonical Snippets Reference

Consult `references/rosetta_stone.md` for full implementation templates across all 17 primitives.
