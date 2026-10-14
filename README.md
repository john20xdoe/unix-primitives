# unix-primitives

> **Stop Inventing Prompt DSLs and Ride 50 Years of Unix Pre-Training Gravity.**

`unix-primitives` is an agent customization suite and workflow engine that replaces fragile natural-language prompt checklists and zero-frequency prompt DSLs (`Freq ≈ 0`) with canonical Unix and computer science formalisms (`Freq > 1,000,000`).

> [!IMPORTANT]
> **Platform Compatibility**: The packaged skills (`/unix-*` slash commands) and installer (`install.sh`) currently target the **Google Antigravity / Gemini CLI** agent environment (`~/.gemini/config/skills/`).
> 
> *Model Agnosticism*: While the skill bundle packaging targets Antigravity, the core Python engines (`state_manager.py`, `unix_primitives.py`), physical `.state/` disk runlevels, and the 17 Unix/CS formalisms are universal and function across any frontier model or harness (Gemini, Claude, OpenAI, Cursor).
>

> [!NOTE]
> This repository is developed with AI assistance, not vibe-coded. All help with further reviewing is deeply-appreciated and welcome.

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

| # | Primitive | Fragile Prompt Replaced | Invariant Enforced | Enforcement |
|---|---|---|---|---|
| **1** | **GNU Makefile DAG** | Step 1 $\rightarrow$ Step 2 $\rightarrow$ Step 3 checklists | Backward-chaining DAG + `mtime` dirty-state invalidation | Host |
| **2** | **SysV `/etc/init.d` Runlevels** | Mutable `PROGRESS.md` | Lexical write-once disk latches (`00_` $\rightarrow$ `99_`) survive 200k+ compaction | Host |
| **3** | **Unix Process Control** | Unbounded subagent memory | Ephemeral child virtual memory; arena GC on `exit 0` | Host |
| **4** | **RFC 5234 EBNF** | Pleading for clean JSON & pause gates | Production grammar with hard XOR mutual exclusion | Prompt-only |
| **5** | **Design-by-Contract** | *"Test edge cases and errors"* | Hoare triples (`@requires`/`@ensures`) + QuickCheck algebraic laws | Prompt-only |
| **6** | **Two-Phase Commit + WAL** | *"Don't leave multi-file edits broken"* | Atomic cross-module transactions (`PREPARE` $\rightarrow$ `COMMIT`/`ROLLBACK`) | Prompt-only |
| **7** | **Circuit Breaker FSM** | *"Try a couple times then stop"* | $k=2$ threshold; `CLOSED` $\rightarrow$ `OPEN` trip halts apology loops | Prompt-only |
| **8** | **`git bisect`** | Linear guessing across files | Midpoint binary search converges in $O(\log_2 N)$ steps | Host |
| **9** | **LKML `[PATCH 0/N]` Series** | *"Make clean, logical commits"* | Topological commit DAG; `git rebase --exec` passes on every commit | Prompt-only |
| **10**| **Multi-Pass Compiler Diagnostics** | *"Review code carefully"* | Structured `error[SCAR-XX]` AST/lifetime/blast-radius passes | Prompt-only |
| **11**| **Stream Demux (`stdout`/`stderr`)** | Mixed JSON data with chat commentary | FD 1 (raw payload) isolated from FD 2 (diagnostics) | Host |
| **12**| **POSIX Signals (`SIGINT`/`SIGTERM`)** | Vague stop/cancel instructions | Explicit signal traps: `SIGINT` checkpoints state, `SIGTERM` rolls back | Host |
| **13**| **Advisory File Locking (`flock`)** | Concurrent agent edit collisions | Atomic `.lock` acquisition eliminates subagent race conditions | Host |
| **14**| **Fail-Fast Shell (`set -euo pipefail`)**| Silent command failure continuation | Zero-tolerance error bubbling halts script on first failure | Host |
| **15**| **Copy-On-Write Scratch Worktrees** | In-place risky speculative edits | Ephemeral `git worktree` sandbox; fast-forward merges only if green | Host |
| **16**| **Least Privilege (`chmod r--`)** | Conversational pleading not to touch files | Hard capability masking (read-only enforcement) | Host |
| **17**| **Ring Buffer & FIFO (`logrotate`)** | Context window log flooding | Bounded token ceiling on terminal output (head 5 + tail 45 lines) | Host |

---

## Slash Command Suite

| Command | Action |
|---|---|
| **`/unix-init <ticket> <title>`** | Physically boots bounded `.state/` directory in workspace with real Makefile |
| **`/unix-stamp <plan\|tdd\|impl>`** | Advances physical runlevel latch with named milestone (`20_plan`, `30_tdd`, `40_impl`) |
| **`/unix-status`** | Inspects active runlevel, physical `mtime` timestamps, and staleness health ($>72\text{h}$) |
| **`/unix-clean`** | Archives completed ticket to flat log and resets active slots to clean slate |
| **`/unix-hook [install\|remove]`** | Optional git pre-push gate (local commits stay safe; push validates milestones) |
| **`/unix-primitives [file\|.agents]`** | **Default command: scan**. Audits prompt file or workspace. Auto-detects local `.agents/` or prompt files if omitted |
| **`/unix-primitives scan <file\|.agents>`** | Explicit audit of prompt file or local `.agents/` folder (rules, skills, workflows). Rejects global paths |
| **`/unix-primitives audit-prompt [file\|.agents]`** | Emits lean, non-paraphrased subagent instruction bundle with telemetry and classification contract |
| **`/unix-primitives delta <orig> <new>`** | Evaluates numeric score delta, % friction reduction, and resolved primitives |
| **`/unix-primitives convert <file>`** | **Non-destructive staging**: Prepares `<file>.NN.converted` for LLM refactoring (original untouched) |
| **`/unix-primitives rewrite <file>`** | **In-place rewrite staging**: Creates `<file>_original` backup before LLM rewrites target in-place |

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
1. **Bounded Storage**: Strictly 6 discrete slots (`00_` $\rightarrow$ `99_`). Directory never exceeds 6 active files ($<50\text{KB}$).
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

## Usage

Step-by-step walkthrough for first-time users:

### Step 1: Audit & Refactor Existing Prompts

#### Audit Friction (Default Behavior):
```text
# Default audit (auto-detects local .agents/, CLAUDE.md, etc.):
/unix-primitives

# Audit specific file directly:
/unix-primitives CLAUDE.md

# Audit entire local .agents/ folder:
/unix-primitives .agents/
# or explicitly with subcommand:
/unix-primitives scan .agents/
```
*(When invoked without a command or target, `/unix-primitives` automatically defaults to `scan`. Directory and multi-file audits leverage an isolated read-only child subagent [Unix Primitive #3: Process Control] fed with the target telemetry and the complete 7 OS Subsystems / 17 Primitives classification contract to deliver a comprehensive **Canonical Architecture Audit** on turn 1 without context bloat or guesswork).*

#### Refactor Prompts Non-Destructively:
```text
/unix-primitives convert CLAUDE.md
```
* **Staging**: The script scans `CLAUDE.md`, computes friction telemetry, and prepares an auto-incrementing non-markdown target `CLAUDE.01.converted` (so agent discovery engines ignore intermediate iterations).
* **Rewrite**: The LLM performs the semantic refactoring into `CLAUDE.01.converted`.
* **Original**: `CLAUDE.md` remains untouched.
* Inspect the diff to compare fragile prose against canonical formalisms:
  ```bash
  diff -u CLAUDE.md CLAUDE.01.converted
  ```
* When ready to apply changes in place:
  ```text
  /unix-primitives rewrite CLAUDE.md
  ```
  *(Prepares `CLAUDE.md_original` backup before LLM updates `CLAUDE.md` in place)*.

---

### Step 2: Initialize Workspace Runtime (When Starting a Task)
When beginning work on a ticket or feature in any repository:

```text
/unix-init PROJ-101 "Implement JWT authentication"
```
* Physically creates `.state/` in repo root with:
  * `.state/00_governance.md` (immutable rules)
  * `.state/10_ticket.md` (task requirements & RFC 822 headers)
  * `.state/Makefile` (real GNU Makefile DAG)
  * `.state/.gitignore` (prevents transient latches from entering git commits)
* Run `state_manager.py link-agents` if local symlinking of skills into `.agents/skills/` is desired.


---

### Step 3: Advance Runlevel Milestones
As development progresses, stamp physical disk latches:

```text
/unix-stamp plan "Architecture approved by reviewer"
/unix-stamp tdd  "Failing reproduction test added"
/unix-stamp impl "Verified implementation passing test suite"
```
* Updates physical disk `mtime`.
* Overwrites volatile pointer `99_next_action.md` in-place ($<200\text{B}$).

---

### Step 4: Check Health & Compaction Recovery
Inspect active runlevel state or recover after a long session:

```text
/unix-status
```
* **Compaction Recovery**: If context resets after long sessions, agent reads physical disk latches and resumes directly from the latest completed milestone.
* **Staleness Check**: Flags tasks older than 72 hours.

---

### Step 5: (Optional) Install Safe Pre-Push Gate
Prevent pushing unverified milestones upstream without interrupting local commits:

```text
/unix-hook install
```
* Commits proceed freely during development.
* `git push` verifies `.state/Makefile` target `ci-gate`.

---

### Step 6: Complete & Reset (Zero Bloat)
When ticket is merged and task is done:

```text
/unix-clean
```
* Archives completed session to flat `.state/archive/PROJ-101.log`.
* Purges active slots back to clean slate (bounded storage without bloat).

---

## Evidence & Empirical Validation

The static **friction score** emitted by `unix_primitives.py` is a linting heuristic measuring prompt adherence and pattern frequency against canonical Unix formalisms. It is **not** an empirical measurement of LLM capability or task performance.

To empirically evaluate agent execution reliability, this repository includes an evaluation harness in `eval/` with a pre-registered methodology.

### The Four Experimental Arms

For each evaluation task, execution reliability is measured across 4 controlled arms:

1. **`prose`**: Baseline unstructured natural-language instructions.
2. **`bespoke`**: Invented domain-specific prompt language / checklist syntax.
3. **`canonical`**: Canonical Unix and Computer Science formalisms.
4. **`host`**: Host-enforced physical latches and OS machine gates (Level 2).

### Pairwise Empirical Hypotheses

| Comparison | Effect Isolated | Scientific Interpretation |
|---|---|---|
| **$\text{canonical} - \text{bespoke}$** | Familiarity & Pre-Training Gravity | Isolates whether using canonical Unix terms outperforms invented syntax due to 50 years of pre-training tokens in frontier model weights. |
| **$\text{bespoke} - \text{prose}$** | Structural Rigor | Measures the reliability benefit of formal syntactic structure over ambiguous English prose. |
| **$\text{host} - \text{canonical}$** | Level 2 vs Level 1 Enforcement | Measures the reliability delta between physical machine gates (filesystem latches, OS process bounds, POSIX file permissions) and prompt-only compliance. |

### Statistical Protocol & Pre-Registration Gate

* **Sample Size**: $N \ge 20$ iterations per (task, arm) cell.
* **Proportion Uncertainty**: Wilson 95% binomial score confidence intervals:
  $$\text{CI}_{95\%} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}} \quad (z = 1.95996)$$
* **Significance Testing**: Two-sided Fisher's exact test on $2 \times 2$ contingency tables ($p < 0.05$).
* **Pre-Registration Gate**: To prevent post-hoc prompt tweaking, `run_ab.py` verifies that `eval/PREREGISTRATION.md` exists and was registered prior to prompt evaluation runs (bypassed with `--no-prereg` in development).

### Running Evaluations

```bash
# Verify the test matrix:
python3 eval/run_ab.py --dry-run

# Run A/B iterations with your agent CLI:
export AGENT_CMD="my-agent --prompt {prompt_file} --dir {task_dir}"
python3 eval/run_ab.py -n 20 --model gpt-4o --seed 42
```

See [eval/README.md](eval/README.md) and [eval/PREREGISTRATION.md](eval/PREREGISTRATION.md) for full harness documentation and registered hypotheses.

---

## License

MIT License. See [LICENSE](LICENSE) for details.



