# Canonical CS & Unix Primitives Reference (17 Primitives / 7 Subsystems)

## 17 Canonical Formalisms

| # | Fragile Prompt Prose (`Freq ≈ 0`) | Canonical CS/Unix Primitive (`Freq > 1,000,000`) | Target Formalism | Enforcement |
|---|-----------------------------------|---------------------------------------------------|------------------|-------------|
| 1 | Numbered checklists, `IF/ELSE/GOTO Step X` | **GNU Makefile DAG** | `.PHONY`, `target: prerequisites`, mtime artifact invalidation | Host |
| 2 | Mutable `PROGRESS.md`, in-context todo tracking | **SysV `/etc/init.d` Runlevels + RFC 822** | `00_` to `99_` lexical file latches, `Key: Value` state headers | Host |
| 3 | Verbose subagent delegation, *"clean up temp files"* | **Unix Process Control** | `fork()`, `waitpid()`, `trap ... EXIT`, arena garbage collection | Host |
| 4 | Formatting begging, premature "Certainly!" promises | **RFC 5234 EBNF & Session Types** | Production rules with XOR gate exclusion + Flores negotiation (?Assert before ?Promise) | Prompt-only |
| 5 | *"Make sure you test edge cases and error handling"* | **Design-by-Contract + QuickCheck** | `@requires`, `@ensures`, `@invariant`, Hoare triples, algebraic laws | Prompt-only |
| 6 | *"Don't leave the repo broken across multiple files"* | **Database WAL + Two-Phase Commit (2PC)** | `BEGIN` $\rightarrow$ `PREPARE` $\rightarrow$ verify all $\rightarrow$ `COMMIT` / `ROLLBACK` | Prompt-only |
| 7 | *"Try a couple times; if stuck, stop and ask me"* | **Circuit Breaker FSM + Idempotency Keys** | `k=2` threshold, `CLOSED` $\rightarrow$ `OPEN` trip, immediate hard halt | Prompt-only |
| 8 | Linear exploration, *"figure out why this test fails"* | **`git bisect` Binary Partitioning** | `mid = (lo + hi) // 2`, $O(\log_2 N)$ search space halving | Host |
| 9 | *"Break your work into clean, logical commits"* | **LKML `[PATCH 0/N]` Series** | Topological commit DAG, `git rebase --exec "make test"` invariant | Prompt-only |
| 10| Polite, superficial review (*"Looks good to me!"*) | **Multi-Pass Compiler Diagnostics** | `error[SCAR-XX]: BLKR/WARN/NIT` with source locations & AST passes | Prompt-only |
| 11| Mixed data payload & chat comments | **Stream Demux (`stdout` vs `stderr`)** | FD 1 (payload) vs FD 2 (diagnostics), exit code | Host |
| 12| Unstructured cancel/stop handling | **POSIX Signals (`SIGINT`, `SIGTERM`, `SIGHUP`)** | Traps for state checkpointing and clean rollback | Host |
| 13| Subagent concurrent write collisions | **Advisory File Locking (`flock(2)` / `.lock`)** | Atomic lock acquisition & release on shared files | Host |
| 14| Permissive silent command failures | **Fail-Fast Shell (`set -euo pipefail`)** | Zero-tolerance error bubbling | Host |
| 15| In-place risky speculative trial edits | **Copy-On-Write Scratch Worktrees** | Ephemeral `git worktree` scratch sandboxing | Host |
| 16| Pleading with agent not to touch files | **Least Privilege & Capabilities (`chmod r--`)** | Structural read-only capability enforcement | Host |
| 17| Context window flooding from long logs | **Ring Buffers & FIFO (`logrotate`)** | Bounded token ceiling on log tailing | Host |

---

## The 7 OS Subsystems

### [1/7] Build & Execution DAGs
* **Primitive**: GNU Makefile DAG (`MAKEFILE_DAG`)
* **Scope**: Sequential checklists, workflows, build/test chains.
* **Invariant**: Backward-chaining DAG + `mtime` invalidation. Targets execute only when dependencies are stale.
* **Enforcement**: Host (`make` engine).

### [2/7] State Persistence & Lifecycle
* **Primitives**: SysV `/etc/init.d` Runlevels (`SYSV_INITD`), POSIX Signals (`POSIX_SIGNALS`)
* **Scope**: Progress tracking, mutable todos, amnesia prevention, cancellation.
* **Invariant**: Externalized disk latches (`00_` to `99_`) with RFC 822 headers survive context compaction. Traps preserve rollback state.
* **Enforcement**: Host (disk latches + signal traps).

### [3/7] Process Isolation & Concurrency
* **Primitives**: Unix Process Control (`PROCESS_ISOLATION`), Advisory File Locking (`FILE_LOCKING`), Least Privilege (`LEAST_PRIVILEGE`)
* **Scope**: Subagent delegation, unbounded context memory, concurrent file access, security boundaries.
* **Invariant**: Subagents act as arena memory allocators (destroyed on exit). File locks prevent concurrent clobbering. Least privilege restricts tool access structurally.
* **Enforcement**: Host (OS process boundary, kernel locks, POSIX permissions).

### [4/7] Protocols & Stream Demux
* **Primitives**: RFC 5234 EBNF & Session Types (`EBNF_GRAMMAR`), Stream Demux (`STREAM_DEMUX`), Ring Buffer (`RING_BUFFER`)
* **Scope**: Output formatting, pause gates, API hallucination prevention, log tailing.
* **Invariant**: Production rules with strict XOR exclusion between tools and pause gates. Segregated stdout (FD 1 payload) vs stderr (FD 2 diagnostics). Ring buffer FIFO tail bounds log token usage.
* **Enforcement**: Prompt-only for EBNF grammar; Host for stream demux and ring buffer FIFO.

### [5/7] Verification & Diagnostics
* **Primitives**: Design-by-Contract (`DESIGN_BY_CONTRACT`), Multi-Pass Compiler Diagnostics (`COMPILER_DIAGNOSTICS`)
* **Scope**: Edge-case testing, code review rigour.
* **Invariant**: Formal pre/post/invariants (@requires/@ensures) + QuickCheck algebraic laws. Multi-pass structured error diagnostics (`error[SCAR-XX]`).
* **Enforcement**: Prompt-only.

### [6/7] Transaction Safety & Fault Tolerance
* **Primitives**: Database WAL + 2PC (`TWO_PHASE_COMMIT`), Circuit Breaker FSM (`CIRCUIT_BREAKER`), Fail-Fast Shell (`FAIL_FAST_SHELL`), Copy-On-Write Worktrees (`SPECULATIVE_COW`)
* **Scope**: Multi-file refactoring, retry loops, error handling, speculative edits.
* **Invariant**: Atomic commit/rollback stages. `k=2` failure threshold halts execution. `set -euo pipefail` halts on errors. Ephemeral worktrees discard failed speculative changes.
* **Enforcement**: Prompt-only for 2PC and Circuit Breaker logic; Host for fail-fast shell and git worktrees.

### [7/7] Search & Commit Topology
* **Primitives**: `git bisect` (`GIT_BISECT`), LKML `[PATCH 0/N]` Series (`LKML_PATCH_SERIES`)
* **Scope**: Regression tracing, commit structuring.
* **Invariant**: Binary space partitioning $O(\log_2 N)$. Topologically ordered commit DAG with per-commit green test verification.
* **Enforcement**: Host for `git bisect`; Prompt-only for LKML patch series.
