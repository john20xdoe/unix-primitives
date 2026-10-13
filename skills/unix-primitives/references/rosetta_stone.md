# Unix & CS Primitives Rosetta Stone

Map fragile prompt prose (`Freq ≈ 0`) to canonical Unix & CS formalisms (`Freq > 1,000,000`). Token-optimized reference catalog.

---

### 1. GNU Makefile DAG (Execution Dependency Graph)
* **Replaces**: *"Do step 1, then step 2. If tests fail return to step 1."*
* **Primitive**:
  ```makefile
  .PHONY: finish ci-gate
  finish: pr-merged
  pr-merged: ci-gate human-landing-approval
  	gh pr merge --squash
  ci-gate: test-green lint-green
  test-green: code-written
  	dart test
  ```
* **Invariant**: Backward-chaining DAG. Leaf file `mtime` modification invalidates downstream targets; forces rerun without English reminders.

---

### 2. SysV `/etc/init.d` + RFC 822 (State Persistence & Latches)
* **Replaces**: *"Keep a PROGRESS.md file updated so you don't forget after compaction."*
* **Primitive**:
  ```text
  state/
    00_governance.md     # Immutable root constraints (read-only)
    10_ticket.md         # Problem spec & acceptance criteria
    20_plan_approved.md  # Human signoff gate (write-once)
    99_next_action.md    # Volatile pointer
  ```
  File header (RFC 822):
  ```rfc822
  Target: ci-gate
  Status: IN_PROGRESS
  Last-Completed: 10_ticket.md
  Next-Action: run_tests
  Idempotency-Key: auth_token_refresh-d41d8cd9
  ```
* **Invariant**: Externalized disk state survives 200k+ token context compaction. Lexical runlevel order (`00_` $\rightarrow$ `99_`) defines boot sequence.

---

### 3. Unix Process Isolation (Memory Management & Subagents)
* **Replaces**: *"Spawn subagent to explore code, make sure it cleans up."*
* **Primitive**:
  ```text
  PID 1 (Orchestrator):
    worker_pid = fork(role="Archaeology", scope="lib/src/*")
    waitpid(worker_pid)  # Blocks; receives exit_code + artifact path
  Worker (Child):
    trap 'rm -rf /tmp/scratch_$$' EXIT
    # Execute deep reads; write findings to disk: state/artifacts/archaeology.md
    exit 0
  ```
* **Invariant**: Context window is non-renewable memory. Process boundary acts as arena garbage collector. Ephemeral child context destroyed on `exit`; orchestrator stays $<30\text{k}$ tokens.

---

### 4. RFC 5234 EBNF (Output Schema & Gate Mutual Exclusion)
* **Replaces**: *"Format output strictly. Do not call tools if waiting for user input."*
* **Primitive**:
  ```ebnf
  turn_response ::= status_header "\n\n" (tool_action | pause_gate)
  status_header ::= "### STATE: " ("RUNNING" | "BLOCKED" | "DONE")
  tool_action   ::= "[EXEC_TOOL: " tool_name "(" [args] ")]"
  pause_gate    ::= "### [PAUSE_GATE: " gate_id "]\n" prompt_text
  (* Invariant: tool_action and pause_gate are strictly mutually exclusive *)
  ```
* **Invariant**: Production rules eliminate parser drift. Enforces hard XOR between autonomous tool dispatch and human pause gate.

---

### 5. Design-by-Contract + QuickCheck (Test Generation)
* **Replaces**: *"Write unit tests and cover edge cases and errors."*
* **Primitive**:
  ```text
  Contract:
    @requires len(input) > 0
    @ensures  decode(encode(x)) == x
    @invariant balance >= 0
  QuickCheck Properties:
    - Idempotence: f(f(x)) == f(x)
    - Conservation: balance_after == balance_before - delta
    - Boundary probe: IEEE-754 NaN/-0.0, surrogate UTF-16 split, integer overflow
  ```
* **Invariant**: Replaces sunny-day tutorial tests with algebraic laws and boundary mutation kills.

---

### 6. Two-Phase Commit + WAL (Atomic Multi-File Migrations)
* **Replaces**: *"Refactor multiple packages without leaving repo in broken state."*
* **Primitive**:
  ```text
  TX [TX-101]:
    PHASE 1 (PREPARE):
      For P in [core, api, cli]:
        Apply diff in scratch worktree
        Vote PREPARED iff `analyze && test` exit 0, else ABORT(log)
    PHASE 2 (DECIDE):
      If ALL vote PREPARED -> Write WAL: COMMIT -> apply to trunk
      Else -> Write WAL: ROLLBACK -> discard worktrees -> halt
  ```
* **Invariant**: Multi-module changes commit atomically or rollback completely. Zero half-applied intermediate states.

---

### 7. Circuit Breaker FSM + Idempotency Keys (Loop Halting)
* **Replaces**: *"Try to fix test failure; if stuck after a couple tries, stop."*
* **Primitive**:
  ```text
  Circuit Breaker Spec:
    threshold: k = 2
    state: CLOSED
  Transitions:
    On failure:
      failures++
      If failures >= 2:
        STATE = OPEN -> HARD HALT. Suppress retry. Escalate to human operator.
  Header: Idempotency-Key: <target_file>:<compiler_error_hash>
  ```
* **Invariant**: Breaks LLM apology death spirals immediately at $k=2$ repeated errors.

---

### 8. Logarithmic Binary Partitioning / `git bisect` (Debugging)
* **Replaces**: *"Inspect code to figure out which step broke."*
* **Primitive**:
  ```text
  Search Space: Stages 1 .. N
  Bounds: low = 1, high = N, max_probes = ceil(log2(N))
  Loop:
    mid = (low + high) // 2
    probe(mid) ? low = mid + 1 : high = mid
    Until low == high -> Offender is Stage low
  ```
* **Invariant**: Replaces linear $O(N)$ random flailing with deterministic $O(\log_2 N)$ search convergence.

---

### 9. LKML `[PATCH 0/N]` Series (Commit Decomposition)
* **Replaces**: *"Break changes into clean, logical commits."*
* **Primitive**:
  ```text
  [PATCH 0/N]: Cover letter architecture DAG
  [PATCH 1/N]: Domain types & contract interfaces
  [PATCH 2/N]: Core state machine & unit tests
  [PATCH N/N]: CLI/UI wiring & integration tests
  Invariant: `git rebase --exec "make test"` passes on every intermediate patch.
  ```
* **Invariant**: Preserves topological ordering and repository bisectability.

---

### 10. Multi-Pass Compiler Diagnostics (Code Review)
* **Replaces**: *"Review code carefully for bugs before submitting."*
* **Primitive**:
  ```text
  Pass 1: AST & Type Soundness
  Pass 2: Resource & Lifetime Safety (leaks, concurrency races)
  Pass 3: Boundary & Blast Radius
  Format:
    error[SCAR-XX]: <defect summary>
      --> <file>:<line>:<col>
       = severity: BLKR | WARN | NIT
       = invariant: <breached rule>
       = fix: <replacement code>
  ```
* **Invariant**: Replaces polite sycophancy with structured static analysis diagnostics.

---

### 11. Stream Demux (`stdout` vs `stderr`)
* **Replaces**: *"Output JSON, but feel free to add your thoughts or progress notes."*
* **Primitive**:
  ```text
  stdout (FD 1): Pure payload (raw JSON / code diff / machine-parsable table).
  stderr (FD 2): Diagnostic logs, human progress messages, warnings.
  exit code: 0 on success, >0 on failure.
  ```
* **Invariant**: Strict separation between data stream and diagnostic stream prevents pipeline parser crashes.

---

### 12. POSIX Signals (Agent Lifecycle & Traps)
* **Replaces**: *"If user asks to stop, finish up nicely and save progress."*
* **Primitive**:
  ```text
  Signal Traps:
    SIGINT  -> trap checkpoint_and_pause: flush state to `99_next_action.md`, yield turn.
    SIGTERM -> trap rollback_and_exit: rollback uncommitted WAL, drop scratch files, exit 0.
    SIGHUP  -> trap reload_rules: reread governance files from disk without resetting task.
  ```
* **Invariant**: Deterministic lifecycle event handlers replace vague shutdown behavior.

---

### 13. Advisory File Locking (`flock(2)` / `.lock` Files)
* **Replaces**: *"Make sure multiple subagents don't edit the same file simultaneously."*
* **Primitive**:
  ```text
  Lock Protocol:
    acquire_lock("<file>.lock", timeout_ms=3000):
      atomically create `<file>.lock` containing `holder: <worker_id>`
      If collision: wait or abort with EWOULDBLOCK.
    release_lock("<file>.lock"): unlink(`<file>.lock`) on finish.
  ```
* **Invariant**: Mutual exclusion eliminates write collisions and race conditions between concurrent agents.

---

### 14. `set -euo pipefail` (Fail-Fast Execution)
* **Replaces**: *"Run these commands, but if anything fails along the way, stop immediately."*
* **Primitive**:
  ```bash
  set -euo pipefail
  # -e: Exit immediately if command exits with non-zero status.
  # -u: Treat unset variables as error.
  # -o pipefail: Return value of pipeline is status of last failed command.
  ```
* **Invariant**: Zero silent error propagation. Halts execution at first point of failure.

---

### 15. Copy-On-Write (COW) Scratch Worktrees (Speculative Edits)
* **Replaces**: *"Try editing the code to see if it works, but undo if it fails."*
* **Primitive**:
  ```bash
  git worktree add -b scratch/tx-101 ../scratch-101 HEAD
  # Run speculative edits & test suite inside ../scratch-101
  # Green: fast-forward merge to main branch.
  # Red: git worktree remove --force ../scratch-101 (zero residual side effects).
  ```
* **Invariant**: Workspace isolation prevents contaminating working tree with failed speculative code.

---

### 16. Principle of Least Privilege & Capabilities (`chmod r--`)
* **Replaces**: *"You are an explorer agent. Only look at files and do not touch anything."*
* **Primitive**:
  ```text
  Execution Context Capabilities:
    CAP_READ_FS: ALLOW
    CAP_WRITE_FS: DENY (no write_to_file / replace_file_content)
    CAP_EXEC_SHELL: DENY (no run_command)
    Umask: 0444 (read-only enforcement)
  ```
* **Invariant**: Security and tool constraints enforced structurally, not by English pleading.

---

### 17. Ring Buffers & Tail Truncation (`logrotate`)
* **Replaces**: *"Don't print too much log output so you don't blow up context."*
* **Primitive**:
  ```text
  Buffer Policy:
    Capacity: N = 50 lines (Ring Buffer / FIFO).
    Eviction: Drop oldest lines on overflow; retain head (first 5 lines) + tail (last 45 lines).
    Emit: "[... skipped M intermediate log lines ...] \n" + tail
  ```
* **Invariant**: Constant token ceiling $O(1)$ on diagnostic outputs regardless of subprocess log volume.
