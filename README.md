# unix-primitives

> **Stop Inventing Prompt DSLs and Ride 50 Years of Unix Pre-Training Gravity.**

`unix-primitives` is an agent customization suite and workflow engine that replaces fragile natural-language prompt checklists and zero-frequency prompt DSLs (`Freq ≈ 0`) with canonical Unix and computer science formalisms (`Freq > 1,000,000`).

> [!IMPORTANT]
> **Platform Compatibility**: The packaged skills (`/unix-*` slash commands) and installer (`install.sh`) currently target the **Google Antigravity / Gemini CLI** agent environment (`~/.gemini/config/skills/`).
> 
> *Model Agnosticism*: While the skill bundle packaging targets Antigravity, the core Python engines (`state_manager.py`, `unix_primitives.py`), physical `.state/` disk runlevels, and the 17 Unix/CS formalisms are universal and function across any frontier model or harness (Gemini, Claude, OpenAI, Cursor).

---

## Acknowledgements & Prior Art

This framework codifies and implements the empirical findings and systems architecture presented by **Randal L. Schwartz** in the article:

* **[What LLMs 'Know' That You Don't Know They Know: Stop Inventing Prompt DSLs and Ride 50 Years of Unix Pre-Training Gravity](https://dev.to/gde/what-llms-know-that-you-dont-know-they-know-stop-inventing-prompt-dsls-and-ride-50-years-of-2bl6)** (Dev.to / GDE Series)
* Related series research:
  * Part 3.6: *Stuart Feldman Was Right in 1976: Why Your AI Agent Needs a Makefile, Not a 20-Step Prompt*
  * Part 3.7: *Surviving the 200k-Token Lobotomy: How Unix init.d and Memento Made My AI Coding Agent Immune to Context Compaction*

Special credit to 50 years of Unix and computer science pioneers—Stuart Feldman, Dave Crocker, Bertrand Meyer, C.A.R. Hoare, Henry Spencer, and the POSIX/IETF/W3C working groups—whose formalisms pre-trained modern frontier models.

---

## The Core Problem: The Zero-Frequency Interpreter Trap

When prompt engineers invent custom numbered checklists or pseudo-code tags (`[CRITICAL_GATE_4]`, `[IF_TEST_FAILS_GOTO_STEP_2]`), their frequency in frontier LLM pre-training corpora is **approximately zero**. 

The model cannot route execution through its deep feed-forward weight circuits; instead, it burns fragile working-memory attention heads simulating an interpreter at runtime. As the context window expands with diffs and compiler output, attention dilutes ($O(1/L)$), causing sequential amnesia, skipped gates, and infinite apology loops.

In contrast, **GNU Makefiles, SysV `/etc/init.d` runlevels, RFC 822 headers, RFC 5234 EBNF grammars, Design-by-Contract, Two-Phase Commit, and Circuit Breakers** appear millions of times in pre-training data. Calling them acts as **static symbol linkage** into crystallized weights.

---

## The 17 Canonical Primitives

| # | Primitive | Fragile Prompt Replaced | Invariant Enforced |
|---|---|---|---|
| **1** | **GNU Makefile DAG** | Step 1 $\rightarrow$ Step 2 $\rightarrow$ Step 3 checklists | Backward-chaining DAG + `mtime` dirty-state invalidation |
| **2** | **SysV `/etc/init.d` Runlevels** | Mutable `PROGRESS.md` | Lexical write-once disk latches (`00_` $\rightarrow$ `99_`) survive 200k+ compaction |
| **3** | **Unix Process Control** | Unbounded subagent memory | Ephemeral child virtual memory; arena GC on `exit 0` |
| **4** | **RFC 5234 EBNF** | Pleading for clean JSON & pause gates | Production grammar with hard XOR mutual exclusion |
| **5** | **Design-by-Contract** | *"Test edge cases and errors"* | Hoare triples (`@requires`/`@ensures`) + QuickCheck algebraic laws |
| **6** | **Two-Phase Commit + WAL** | *"Don't leave multi-file edits broken"* | Atomic cross-module transactions (`PREPARE` $\rightarrow$ `COMMIT`/`ROLLBACK`) |
| **7** | **Circuit Breaker FSM** | *"Try a couple times then stop"* | $k=2$ threshold; `CLOSED` $\rightarrow$ `OPEN` trip halts apology loops |
| **8** | **`git bisect`** | Linear guessing across files | Midpoint binary search converges in $O(\log_2 N)$ steps |
| **9** | **LKML `[PATCH 0/N]` Series** | *"Make clean, logical commits"* | Topological commit DAG; `git rebase --exec` passes on every commit |
| **10**| **Multi-Pass Compiler Diagnostics** | *"Review code carefully"* | Structured `error[SCAR-XX]` AST/lifetime/blast-radius passes |
| **11**| **Stream Demux (`stdout`/`stderr`)** | Mixed JSON data with chat commentary | FD 1 (raw payload) isolated from FD 2 (diagnostics) |
| **12**| **POSIX Signals (`SIGINT`/`SIGTERM`)** | Vague stop/cancel instructions | Explicit signal traps: `SIGINT` checkpoints state, `SIGTERM` rolls back |
| **13**| **Advisory File Locking (`flock`)** | Concurrent agent edit collisions | Atomic `.lock` acquisition eliminates subagent race conditions |
| **14**| **Fail-Fast Shell (`set -euo pipefail`)**| Silent command failure continuation | Zero-tolerance error bubbling halts script on first failure |
| **15**| **Copy-On-Write Scratch Worktrees** | In-place risky speculative edits | Ephemeral `git worktree` sandbox; fast-forward merges only if green |
| **16**| **Least Privilege (`chmod r--`)** | Conversational pleading not to touch files | Hard capability masking (read-only enforcement) |
| **17**| **Ring Buffer & FIFO (`logrotate`)** | Context window log flooding | Constant $O(1)$ token ceiling on terminal output (head 5 + tail 45 lines) |

---

## Slash Command Suite

| Command | Action |
|---|---|
| **`/unix-init <ticket> <title>`** | Physically boots bounded `.state/` directory in workspace with real Makefile |
| **`/unix-stamp <plan\|tdd\|impl>`** | Advances physical runlevel latch with named milestone (`20_plan`, `30_tdd`, `40_impl`) |
| **`/unix-status`** | Inspects active runlevel, physical `mtime` timestamps, and staleness health ($>72\text{h}$) |
| **`/unix-clean`** | Archives completed ticket to flat log and resets active slots to clean slate |
| **`/unix-hook [install\|remove]`** | Optional git pre-push gate (local commits stay safe; push validates milestones) |
| **`/unix-primitives convert <file>`** | Refactors existing prompt/rules files into canonical CS formalisms |

---

## Physical Disk State Engine (`.state/`)

To survive context compactions and memory truncation, states are grounded physically on disk:

```text
.state/
  .gitignore           # Blocks transient state from entering git commits or PR diffs
  Makefile             # Real GNU Makefile connecting physical disk target stamps
  00_governance.md     # Immutable project invariants (read-only)
  10_ticket.md         # Active ticket spec + RFC 822 headers
  20_plan.md           # Physical signoff latch (write-once)
  30_tdd_red.md        # Physical failing test verification latch
  40_impl_green.md     # Physical green build verification latch
  99_next_action.md    # Volatile pointer (overwritten in-place, <200B)
```

### Anti-Bloat & Anti-Staleness Guarantees
1. **$O(1)$ Bounded Storage**: Strictly 6 discrete slots (`00_` $\rightarrow$ `99_`). Directory never exceeds 6 active files ($<50\text{KB}$).
2. **In-Place Overwrites**: `99_next_action.md` is overwritten in place every turn, never appended.
3. **Repository Cleanliness**: `.state/.gitignore` isolates transient latches from git staging and PR diffs.
4. **Archive & Prune**: `/unix-clean` rolls finished tickets into `.state/archive/<ticket>.log` and purges active slots.
5. **Staleness Expiry**: Tickets older than 72 hours are flagged as `STALE`.

---

## Installation

Clone and run the installer:

```bash
git clone https://github.com/john20xdoe/unix-primitives.git
cd unix-primitives

# Live Symlink mode (Default - edits in repo reflect immediately in agent)
./install.sh
# or explicitly:
./install.sh --symlink

# Static Copy mode (Copies files without symlinking to repo)
./install.sh --copy
```

### Installation Modes
* `--symlink` (**Default**): Establishes live symlinks from `skills/*` to `~/.gemini/config/skills/`. Any edits or git updates in this repository take effect immediately across all agent sessions without re-running install.
* `--copy`: Performs standalone `cp -R` into `~/.gemini/config/skills/`. Useful if running on systems that restrict symlinks or when wanting disconnected snapshot.


---

## License

MIT License. See [LICENSE](LICENSE) for details.

