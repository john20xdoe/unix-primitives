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

Maps fragile natural-language prompts, numbered checklists, and zero-frequency prompt DSLs (`Freq ≈ 0`) to canonical Unix and computer science formalisms (`Freq > 1,000,000`).

The CLI scripts (`unix_primitives.py`, `state_manager.py`) scan files, calculate friction scores, manage `.state/` disk latches, and prepare output target paths or backups. The LLM performs the semantic prompt refactoring and rewrites.

---

## Commands & Triggers

| Command | Action | Output / Target |
|---------|--------|-----------------|
| `/unix-primitives [path]` | Friction scan audit (default) | Telemetry report & friction score |
| `/unix-primitives scan <path>` | Explicit friction scan | Telemetry report & friction score |
| `/unix-primitives convert <path>` | Non-destructive rewrite staging | Prepares `<path>.NN.converted`; LLM writes refactored prompt |
| `/unix-primitives rewrite <path>` | In-place rewrite staging | Backs up `<path>_original`; LLM rewrites `<path>` |
| `/unix-primitives delta <orig> <new>` | Compare friction scores | Score delta, % reduction, resolved primitives |
| `/unix-primitives generate <task>` | Synthesize canonical prompt | Generates prompt using Unix formalisms |
| `/unix-init [ticket] [title]` | Initialize disk state | Provisions `.state/` directory with runlevel latches |
| `/unix-stamp <slot> "<summary>"` | Record milestone latch | Stamps `plan`, `tdd`, or `impl` runlevel to disk |
| `/unix-status` | Inspect disk runlevels | Shows active milestone latches and staleness |
| `/unix-clean` | Reset workspace state | Archives completed ticket to flat log; clears slots |
| `/unix-hook [install\|remove]` | Manage git pre-push hook | Verifies `.state/` milestone targets on `git push` |

References:
* Primitives & 7 Subsystems catalog: [references/primitives.md](references/primitives.md)
* Subagent delegation protocol: [references/delegation.md](references/delegation.md)
* Complete examples and templates: [references/rosetta_stone.md](references/rosetta_stone.md)

---

## Execution Protocols

### 1. Scan Mode (`/unix-primitives [path]` or bare `/unix-primitives`)
1. **Default Action is `scan`**: Never halt or query user for subcommand when target is given without a verb.
2. **Target Resolution**: Auto-detects local `.agents/`, `CLAUDE.md`, `.cursorrules`, or `README.md` if omitted.
3. **Execution**:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py scan "<path>"
   # or test snippet via stdin:
   echo "<content>" | python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py scan - --score-only
   ```
4. **Report**: Emit friction score, detected anti-patterns, subsystem matches, and actionable next steps. For directory trees, see delegation protocol in [references/delegation.md](references/delegation.md).

### 2. Convert / Rewrite Mode (`/unix-primitives convert | rewrite <path>`)
The `unix_primitives.py` script prepares paths and safety backups; the LLM performs the refactoring:
1. **Staging**:
   * `convert`: Runs script to get `<path>.NN.converted` target. Original file remains untouched.
     ```bash
     python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py convert "<path>"
     ```
   * `rewrite`: Runs script to create `<path>_original` backup before in-place modification.
     ```bash
     python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py rewrite "<path>"
     ```
2. **Refactoring Rules**:
   * Replace linear instructions with backward-chaining Makefile targets or explicit FSMs.
   * Replace mutable progress tracking with `/etc/init.d` disk latches and RFC 822 headers.
   * Replace vague retry advice with a Circuit Breaker FSM (`k=2`).
   * Replace "test edge cases" with Hoare contracts (`@requires`, `@ensures`).
   * Replace prose output demands with strict RFC 5234 EBNF grammars.
   * **Domain Invariant**: NEVER change existing file paths, variable names, shell commands, or business logic.
3. **Verification**: Run `delta` to confirm score reduction:
   ```bash
   python3 ~/.gemini/config/skills/unix-primitives/scripts/unix_primitives.py delta "<original>" "<rewritten>"
   ```

### 3. Generate Mode (`/unix-primitives generate <task>`)
Synthesize new guidelines or workflows using canonical formalisms:
* Multi-step workflows -> GNU `Makefile` DAG.
* State tracking -> `.state/` runlevel latches (`00_` to `99_`) with RFC 822 headers.
* Retry loops -> Circuit Breaker (`k=2`).
* Structured responses -> RFC 5234 EBNF with XOR gate mutual exclusion.

### 4. Disk State Lifecycle (`/unix-init`, `/unix-stamp`, `/unix-clean`)
1. **Initialize**: `/unix-init <ticket-id> "<title>"` provisions `.state/` with `00_governance.md`, `10_ticket.md`, `99_next_action.md`, and real `Makefile`.
2. **Stamp Milestones**:
   * `/unix-stamp plan "<summary>"` -> `.state/20_plan.md` (write-once signoff gate; override with `--force`).
   * `/unix-stamp tdd "<summary>"` -> `.state/30_tdd_red.md` (failing reproduction tests).
   * `/unix-stamp impl "<summary>"` -> `.state/40_impl_green.md` (passing implementation).
3. **Volatile Pointer**: `99_next_action.md` is updated in-place each turn.
4. **Clean**: `/unix-clean` archives completed ticket latches to `.state/archive/<ticket>.log` and resets transient slots.
