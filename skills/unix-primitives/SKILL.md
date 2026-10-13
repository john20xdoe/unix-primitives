---
name: unix-primitives
description: >
  Refactor, convert, or generate system prompts, agent skills, cursorrules, CLAUDE.md,
  workflows, and README guidelines into canonical Unix & computer science primitives (Makefile DAGs,
  /etc/init.d runlevel latches, RFC 822 headers, RFC 5234 EBNF, Design-by-Contract,
  Circuit Breakers, 2PC/WAL, git bisect, LKML patch series, compiler diagnostics).
  Eliminates fragile English checklists and zero-frequency prompt DSLs by leveraging 50 years
  of pre-training weight gravity.
  Trigger: /unix-primitives [convert|generate|scan] <path|prompt>, "convert prompt to unix primitives",
  "apply pre-training gravity", "unix prompt converter", "refactor prompt to unix".
---

# Unix Primitives (Pre-Training Gravity Skill)

## Purpose

Transforms fragile natural-language prompts, numbered checklists, and zero-frequency prompt DSLs (`Freq ≈ 0`) into canonical Unix and computer science formalisms (`Freq > 1,000,000`).

Bespoke prompt DSLs force frontier LLMs to simulate interpreters inside fragile working-memory attention heads, causing attention dilution ($O(1/L)$), sequential amnesia, and skipped gates. In contrast, 50-year-old Unix formalisms trigger deep, pre-trained feed-forward circuits ("static symbol linkage"), freeing working memory for actual code synthesis.

---

## Triggers & Usage

* `/unix-primitives convert <filepath>`: Non-destructive conversion. Writes refactored output to `<filepath>.NN.md` (e.g. `CLAUDE.01.md`), leaving original untouched.
* `/unix-primitives rewrite <filepath>`: In-place rewrite. Saves backup to `<filepath>.original.md` and updates original file.
* `/unix-primitives generate <task description>`: Generate brand-new skill, prompt, workflow, or ruleset architected entirely with canonical formalisms.
* `/unix-primitives scan <filepath>`: Non-destructive analysis reporting friction score and mapping recommendations.

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
| 4 | Paragraphs begging for strict formatting & pause gates | **RFC 5234 EBNF Grammars** | Production rules with XOR mutual exclusion between gate & tools |
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

### Mode 1: Convert / Rewrite Existing File (`/unix-primitives convert | rewrite <path>`)

1. **Scan Target**:
   Run scanner to inspect anti-pattern matches and determine output path:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py convert "<path>"
   ```
2. **Determine Target Destination**:
   * **`convert` (Default — Non-Destructive)**: Generates refactored output in `<path>.NN.md` (e.g. `CLAUDE.01.md`, `README.01.md`). The original file remains untouched.
   * **`rewrite` (In-Place)**: Saves backup to `<path>.original.md` before overwriting `<path>`.
3. **Refactor Invariants**:
   * Replace linear instructions with backward-chaining Makefile targets or explicit FSMs.
   * Replace mutable progress tracking with `/etc/init.d`-style disk latches and RFC 822 headers.
   * Replace vague retry advice with a 6-line Circuit Breaker state machine (`threshold k=2`).
   * Replace "test edge cases" with Hoare contracts (`@requires`, `@ensures`) and QuickCheck laws.
   * Replace prose output demands with strict RFC 5234 EBNF production rules.
4. **Preserve Domain Code & Paths Verbatim**:
   * **NEVER** modify existing file paths, variable names, shell commands, or repo-specific business logic.
   * Only refactor the *control flow, execution invariants, state tracking, and protocol definitions*.
5. **Report Score Delta**:
   Display before/after friction analysis and target destination path.


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
