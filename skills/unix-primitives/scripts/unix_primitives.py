#!/usr/bin/env python3
"""
unix_primitives.py - Scanner and refactoring utility for prompt gravity.

Analyzes prompts, skills, workflows, and system guidelines for zero-frequency
anti-patterns and reports or maps them to canonical Unix & CS formalisms.
"""

import sys
import os
import re
import argparse
from typing import List, Dict, Optional

PATTERNS = [
    {
        "id": "MAKEFILE_DAG",
        "name": "Imperative Execution Checklist / GOTO Loop",
        "regex": r"(?i)(?:step\s*\d+[:\.]?[\s\S]{1,60}(?:then|next|after|goto|return\s*to)|(?:\b1\.\s+[^\n]+(?:\n\s*2\.\s+[^\n]+)+)|(?:first\b[\s\S]{1,60}\bthen\b[\s\S]{1,60}\b(?:finally|after))|#+\s*(?:workflow|pipeline|execution\s+steps?|steps\s+to\s+follow|order\s+of\s+operations)|(?:before\s+(?:proceeding|moving\s+to|continuing)|prerequisite|depends\s+on\s+step))",
        "canonical": "GNU Makefile DAG (target: prerequisites, .PHONY)",
        "explanation": "Replace linear checklist with backward-chaining Makefile targets and file mtime invalidation.",
        "snippet": """.PHONY: finish ci-gate
finish: pr-merged
pr-merged: ci-gate human-landing-approval
ci-gate: test-green lint-green"""
    },
    {
        "id": "SYSV_INITD",
        "name": "Mutable Progress State / Compaction Amnesia",
        "regex": r"(?i)(?:-\s*\[[ xX]?\]|(?:track|maintain|update|log|record)\s+(?:your\s+)?(?:progress|status|state|tasks?|todos?|checklist|steps?|scratchpad)|#+\s*(?:tasks?|todo|progress|checklist|current\s+state)|(?:mark\s+(?:tasks?|steps?|items?)\s+as\s+(?:done|complete)|check\s+off)|(?:keep\s+track\s+of|remember\s+(?:what|which)\s+steps|scratchpad|memory\s+bank))",
        "canonical": "SysV /etc/init.d Runlevels (00_... -> 99_...) + RFC 822 Headers",
        "explanation": "Externalize state to disk-backed immutable lexical latches with RFC 822 key-value headers.",
        "snippet": """state/
  00_governance.md     (immutable read-only)
  10_ticket.md         (requirements)
  20_plan_approved.md  (human signoff latch)
  99_next_action.md    (volatile pointer)"""
    },
    {
        "id": "PROCESS_ISOLATION",
        "name": "Unbounded Context Subagent Delegation",
        "regex": r"(?i)(?:\b(?:subagents?|sub-agents?|child\s+agents?|worker\s+agents?)\b|(?:spawn|delegate\s+to)\s+(?:an?\s+)?(?:subagent|child\s+agent|worker|agent)|(?:clean\s+up|delete|remove)\s+(?:temporary|temp|scratch)\s+(?:files?|artifacts?))",
        "canonical": "Unix Process Control (fork() / waitpid() / trap EXIT)",
        "explanation": "Treat process boundaries as arena garbage collectors. Retain compact orchestrator context (<30k tokens).",
        "snippet": """PID 1 (Orchestrator): fork(role="Archaeology") -> waitpid()
Child: trap 'rm -rf /tmp/scratch_$$' EXIT -> write disk artifact -> exit 0"""
    },
    {
        "id": "EBNF_GRAMMAR",
        "name": "Unconstrained Response Output / Gate Conflict",
        "regex": r"(?i)(?:(?:format|respond|output)\s+(?:only\s+as|strictly|must\s+be)\s+(?:in|as)?\s*(?:json|xml|yaml|markdown|csv)|(?:do\s+not\s+(?:include|emit|output)\s+(?:any\s+)?(?:prose|text|comments?|explanation)|raw\s+json\s+only)|(?:wait\s+for\s+(?:user|human)\s+(?:confirmation|approval|response)|stop\s+and\s+ask|pause\s+before|ask\s+(?:the\s+)?user\s+before)|(?:never\s+call\s+tools?\s+(?:when|while|if)\s+asking|do\s+not\s+call\s+tools?\s+and\s+ask))",
        "canonical": "RFC 5234 EBNF Grammar (Strict Mutual Exclusion)",
        "explanation": "Constrain turn response structure using production rules with hard XOR exclusivity.",
        "snippet": """turn_response ::= status_header "\\n\\n" (tool_action | pause_gate)
(* Invariant: tool_action and pause_gate are strictly mutually exclusive *)"""
    },
    {
        "id": "DESIGN_BY_CONTRACT",
        "name": "Sunny-Day / Vague Test Prompting",
        "regex": r"(?i)(?:(?:test|cover)\s+(?:all\s+)?(?:edge\s*cases?|corner\s*cases?|boundary|failures?|errors?)|(?:ensure|verify|make\s+sure)\s+(?:that\s+)?(?:all\s+)?tests?\s+pass|(?:write\s+(?:unit\s+)?tests?|tdd|test-driven)\s+(?:first|before|for\s+every)|(?:acceptance\s+criteria|preconditions?|postconditions?|invariants?))",
        "canonical": "Design-by-Contract (@requires, @ensures) + QuickCheck Laws",
        "explanation": "Specify formal Hoare pre/post conditions and algebraic laws (idempotence, round-trip) to kill boundary mutants.",
        "snippet": """@requires tokens > 0
@ensures  result == true ==> balance == old(balance) - tokens
@invariant balance >= 0
QuickCheck Laws: idempotence, round-trip, boundary probe"""
    },
    {
        "id": "TWO_PHASE_COMMIT",
        "name": "Unhedged Multi-File / Monorepo Refactoring",
        "regex": r"(?i)(?:refactor(?:ing)?\s+across\s+(?:multiple\s+files|modules|packages)|(?:do\s+not|never)\s+leave\s+(?:the\s+)?(?:codebase|repo|build|tests?)\s+(?:broken|failing|inconsistent)|(?:atomic\s+(?:changes?|updates?|edits?|commits?)|all\s+or\s+nothing\s+changes?))",
        "canonical": "Database WAL + Two-Phase Commit (2PC: PREPARE -> COMMIT/ROLLBACK)",
        "explanation": "Enforce atomic cross-package mutations. Commit iff all participants vote PREPARED, else full ROLLBACK.",
        "snippet": """PHASE 1 (PREPARE): Verify scratch worktree per participant
PHASE 2 (DECIDE): If all PREPARED -> COMMIT, else ROLLBACK"""
    },
    {
        "id": "CIRCUIT_BREAKER",
        "name": "Apology Death Spiral / Unbounded Retries",
        "regex": r"(?i)(?:(?:if\s+(?:it|tests?|build|command)\s+fails?|on\s+failure)[\s\S]{1,60}(?:try\s+again|retry|keep\s+trying|fix\s+(?:it|the\s+error)|re-run)|(?:retry\s+until|repeat\s+until|loop\s+until|try\s+up\s+to\s+\d+\s+times)|(?:if\s+(?:you\s+get\s+)?stuck|when\s+stuck|after\s+\d+\s+failures))",
        "canonical": "Distributed Circuit Breaker FSM (CLOSED -> OPEN) + Idempotency Keys",
        "explanation": "Halt repetitive retry loops after k=2 failures. Trip to OPEN state and escalate immediately.",
        "snippet": """threshold: k=2
If failures >= 2: STATE = OPEN -> HARD HALT. Suppress retry. Escalate to human."""
    },
    {
        "id": "GIT_BISECT",
        "name": "Linear Flailing / Guess-Based Debugging",
        "regex": r"(?i)(?:figure\s+out\s+why\s+(?:this|the|it)|find\s+(?:which\s+commit|what)\s+broke|locate\s+(?:the\s+)?regression|trace\s+(?:the\s+)?root\s+cause|binary\s+search\s+commits)",
        "canonical": "git bisect (Logarithmic Binary Search O(log2 N))",
        "explanation": "Partition causal search space into binary halves using midpoint probes rather than linear scans.",
        "snippet": """mid = (low + high) // 2
Probe mid -> adjust bounds -> converge in ceil(log2 N) steps."""
    },
    {
        "id": "LKML_PATCH_SERIES",
        "name": "Vague Commit Decomposition",
        "regex": r"(?i)(?:(?:clean|logical|atomic|small)\s+commits?|break\s+(?:down\s+)?changes\s+into\s+commits|commit\s+messages?\s+(?:guidelines?|format|convention)|conventional\s+commits?|\b(?:feat|fix|chore|refactor|docs|test)\s*\(?[^)]*\)?\s*:)",
        "canonical": "LKML [PATCH 0/N] Series + git rebase --exec",
        "explanation": "Require topological commit series where every intermediate commit independently compiles and tests pass.",
        "snippet": """[PATCH 0/N]: Architecture DAG
[PATCH 1/N]: Domain interfaces & types
[PATCH N/N]: Wireup & integration tests
Invariant: git rebase --exec "make test" passes on every commit."""
    },
    {
        "id": "COMPILER_DIAGNOSTICS",
        "name": "Polite / Superficial Code Review",
        "regex": r"(?i)(?:code\s*review|review\s+(?:the\s+)?(?:code|changes?|diff|pr|pull\s*request)|check\s+(?:code\s+)?for\s+(?:bugs?|errors?|issues?|code\s+smells?|regressions?)|verify\s+(?:code\s+quality|clean\s+code|correctness))",
        "canonical": "Multi-Pass Compiler Diagnostics Pipeline (error[SCAR-XX])",
        "explanation": "Replace peer compliments with structured static analysis passes (AST -> Lifetimes -> Blast Radius).",
        "snippet": """error[SCAR-XX]: <defect summary>
  --> <file>:<line>:<col>
   = severity: BLKR | WARN | NIT
   = invariant: <breached rule>
   = fix: <concrete diff>"""
    },
    {
        "id": "STREAM_DEMUX",
        "name": "Mixed Data Payload & Human Prose",
        "regex": r"(?i)(?:output\s+(?:json|yaml|data)[\s\S]{1,60}(?:explain|comments?|notes?|thoughts?)|mix\s+(?:data|json)\s+with\s+(?:text|comments?)|(?:return\s+only\s+(?:the\s+)?(?:code|diff|patch|json)|no\s+conversational\s+(?:text|filler|comments?)))",
        "canonical": "POSIX Stream Demux (stdout FD 1 vs stderr FD 2)",
        "explanation": "Strictly segregate machine-parsable payloads (stdout) from diagnostic notes (stderr).",
        "snippet": """stdout (FD 1): Pure payload (raw JSON / diff / AST).
stderr (FD 2): Diagnostic progress & human notes.
exit code: 0 on success, >0 on failure."""
    },
    {
        "id": "POSIX_SIGNALS",
        "name": "Vague Teardown / Interruption Handling",
        "regex": r"(?i)(?:if\s+(?:user\s+)?(?:cancels|stops|aborts|interrupts)|handle\s+(?:cancellation|interruption|shutdown)|graceful\s+(?:shutdown|teardown|exit)|clean\s+up\s+on\s+exit)",
        "canonical": "POSIX Signal Handlers (SIGINT, SIGTERM, SIGHUP)",
        "explanation": "Bind interruptions to deterministic signal traps: SIGINT (checkpoint), SIGTERM (rollback & clean exit).",
        "snippet": """SIGINT  -> trap checkpoint_and_pause: flush state to `99_next_action.md`
SIGTERM -> trap rollback_and_exit: rollback uncommitted WAL, exit 0"""
    },
    {
        "id": "FILE_LOCKING",
        "name": "Unsynchronized Concurrent Agent Writes",
        "regex": r"(?i)(?:concurrent\s+(?:writes?|edits?|agents?)|avoid\s+(?:conflicting\s+edits?|race\s+conditions?|concurrent\s+conflicts?)|make\s+sure\s+(?:agents?|subagents?)\s+don'?t\s+overwrite|file\s+locks?)",
        "canonical": "Advisory File Locking (flock(2) / <file>.lock)",
        "explanation": "Enforce atomic lockfile acquisition before mutating files across concurrent subagents.",
        "snippet": """acquire_lock("<file>.lock", timeout_ms=3000)
# mutate file
release_lock("<file>.lock")"""
    },
    {
        "id": "FAIL_FAST_SHELL",
        "name": "Permissive / Silent Command Error Swallowing",
        "regex": r"(?i)(?:(?:stop|abort|fail|halt)\s+(?:immediately\s+)?(?:if|on)\s+(?:any\s+)?(?:error|failure|command\s+fails)|set\s+-e|fail[- ]fast\s+shell|(?:run|execute)\s+commands?[\s\S]{1,60}(?:abort|stop)\s+on\s+error)",
        "canonical": "set -euo pipefail (Fail-Fast Shell Invariant)",
        "explanation": "Enforce strict zero-tolerance error propagation on script execution.",
        "snippet": """set -euo pipefail
# -e: exit on error
# -u: error on unset variable
# -o pipefail: fail if any pipe segment fails"""
    },
    {
        "id": "SPECULATIVE_COW",
        "name": "Unhedged In-Place Trial Edits",
        "regex": r"(?i)(?:try\s+(?:an?\s+)?edit[\s\S]{1,60}(?:undo|revert)|speculative\s+changes?|git\s+worktree|scratch\s+worktree|temporary\s+branch[\s\S]{1,60}revert)",
        "canonical": "Copy-On-Write Scratch Worktrees (git worktree)",
        "explanation": "Isolate experimental mutations in ephemeral git worktree; fast-forward merge only on test pass.",
        "snippet": """git worktree add -b scratch/tx ../scratch-tx HEAD
# test passes -> fast-forward merge
# test fails -> git worktree remove --force ../scratch-tx"""
    },
    {
        "id": "LEAST_PRIVILEGE",
        "name": "Vague Role-Based Behavioral Pleading",
        "regex": r"(?i)(?:(?:do\s+not|never)\s+(?:modify|edit|change|touch|write\s+to|delete)\s+(?:any\s+)?(?:files?|code)|read[- ]only\s+mode|only\s+(?:read|look|inspect|explore)|prohibited\s+from\s+(?:editing|modifying|writing))",
        "canonical": "Principle of Least Privilege / Capabilities (chmod r--)",
        "explanation": "Enforce tool restrictions structurally at permission mask level rather than conversational pleading.",
        "snippet": """Capabilities:
  CAP_READ_FS: ALLOW
  CAP_WRITE_FS: DENY (strip write_to_file / replace_file_content)
  CAP_EXEC_SHELL: DENY"""
    },
    {
        "id": "RING_BUFFER",
        "name": "Unbounded Log Output / Context Flooding",
        "regex": r"(?i)(?:(?:limit|truncate|tail|head)\s+(?:long\s+)?(?:logs?|terminal\s+output|dumps?)|(?:don'?t|avoid)\s+(?:dumping|printing)\s+(?:too\s+much\s+log|long\s+logs?)|save\s+tokens?\b|economize\s+tokens?\b|context\s+(?:bloat|flooding))",
        "canonical": "Circular Ring Buffer / Tail Truncation (logrotate)",
        "explanation": "Cap tool output with constant-bound FIFO ring buffer: retain head (5 lines) + tail (45 lines).",
        "snippet": """Buffer Capacity: N = 50 lines (Ring Buffer)
Overflow: drop intermediate lines -> emit: "[... skipped M lines ...]\\n" + tail"""
    }
]

def scan_text(text: str) -> List[Dict]:
    findings = []
    for p in PATTERNS:
        matches = list(re.finditer(p["regex"], text))
        if matches:
            findings.append({
                "pattern": p,
                "matches": [m.group(0) for m in matches]
            })
    return findings

SUBSYSTEMS = [
    {
        "id": "BUILD_EXECUTION",
        "num": 1,
        "name": "Build & Execution DAGs",
        "canonical": "GNU Makefile DAG",
        "primitives": ["MAKEFILE_DAG"],
        "description": "Deterministic dependency graphs, target invalidation (.PHONY, mtime)",
    },
    {
        "id": "STATE_LIFECYCLE",
        "num": 2,
        "name": "State Persistence & Lifecycle",
        "canonical": "SysV Runlevels + RFC 822 / POSIX Signals",
        "primitives": ["SYSV_INITD", "POSIX_SIGNALS"],
        "description": "Compaction-immune disk latches (00_ -> 99_) & signal traps (SIGINT/SIGTERM)",
    },
    {
        "id": "PROCESS_CONCURRENCY",
        "num": 3,
        "name": "Process Isolation & Concurrency",
        "canonical": "Unix Process Control / flock(2) / Least Privilege",
        "primitives": ["PROCESS_ISOLATION", "FILE_LOCKING", "LEAST_PRIVILEGE"],
        "description": "Arena memory reclamation (fork/waitpid/trap EXIT), file locking, capability masks",
    },
    {
        "id": "PROTOCOLS_STREAM",
        "num": 4,
        "name": "Protocols & Stream Demux",
        "canonical": "RFC 5234 EBNF / Stream Demux / Ring Buffer",
        "primitives": ["EBNF_GRAMMAR", "STREAM_DEMUX", "RING_BUFFER"],
        "description": "XOR gate production rules, stdout/stderr segregation, O(1) ring buffers",
    },
    {
        "id": "VERIFICATION_DIAGNOSTICS",
        "num": 5,
        "name": "Verification & Diagnostics",
        "canonical": "Design-by-Contract / Multi-Pass Compiler Diagnostics",
        "primitives": ["DESIGN_BY_CONTRACT", "COMPILER_DIAGNOSTICS"],
        "description": "Hoare contracts (@requires/@ensures), QuickCheck laws, structured error[SCAR-XX]",
    },
    {
        "id": "TRANSACTION_SAFETY",
        "num": 6,
        "name": "Transaction Safety & Fault Tolerance",
        "canonical": "WAL + 2PC / Circuit Breaker / Fail-Fast Shell / COW Worktrees",
        "primitives": ["TWO_PHASE_COMMIT", "CIRCUIT_BREAKER", "FAIL_FAST_SHELL", "SPECULATIVE_COW"],
        "description": "Atomic cross-module transactions, k=2 circuit breaker, set -euo pipefail, git worktree",
    },
    {
        "id": "TOPOLOGY_SEARCH",
        "num": 7,
        "name": "Search & Commit Topology",
        "canonical": "git bisect / LKML [PATCH 0/N] Series",
        "primitives": ["GIT_BISECT", "LKML_PATCH_SERIES"],
        "description": "O(log2 N) binary search partitioning, topologically ordered bisectable commit series",
    },
]

PRIMITIVE_MAP = {p["id"]: p for p in PATTERNS}
PRIMITIVE_SUBSYSTEM_MAP = {}
for sub in SUBSYSTEMS:
    for pid in sub["primitives"]:
        PRIMITIVE_SUBSYSTEM_MAP[pid] = sub

def calculate_friction_score(findings: List[Dict], total_lines: int) -> int:
    if not findings:
        return 0
    raw_score = sum(len(f["matches"]) * 10 for f in findings)
    return min(100, max(15, raw_score))

def classify_file_suitability(content: str, rel_path: str, findings: List[Dict]) -> Dict:
    finding_ids = {f["pattern"]["id"] for f in findings}
    lines_lower = content.lower()
    
    detected_primitives: Dict[str, str] = {}
    
    # 1. MAKEFILE_DAG
    if "MAKEFILE_DAG" in finding_ids:
        detected_primitives["MAKEFILE_DAG"] = "Sequential execution checklist / workflow GOTO loop"
    elif any(k in lines_lower for k in ["workflow", "pipeline", "execution step", "steps to follow", "build steps", "ci-gate"]):
        detected_primitives["MAKEFILE_DAG"] = "Multi-stage process / execution pipeline"
    elif re.search(r"```(?:bash|sh)\b[\s\S]*?(?:npm|pytest|cargo|make|python3|pip|docker|git|mvn|gradle)", content):
        detected_primitives["MAKEFILE_DAG"] = "Chains shell build/test commands into targets"

    # 2. SYSV_INITD
    if "SYSV_INITD" in finding_ids:
        detected_primitives["SYSV_INITD"] = "Mutable task tracking / compaction-vulnerable scratchpad"
    elif re.search(r"-\s*\[[ xX]?\]", content) or any(k in lines_lower for k in ["todo", "checklist", "progress tracking", "task list", "scratchpad"]):
        detected_primitives["SYSV_INITD"] = "Interactive todo/checklist -> Externalize to physical disk latches (00_ to 99_)"

    # 3. PROCESS_ISOLATION
    if "PROCESS_ISOLATION" in finding_ids:
        detected_primitives["PROCESS_ISOLATION"] = "Subagent delegation / memory management"
    elif any(k in lines_lower for k in ["subagent", "sub-agent", "child agent", "worker agent", "delegate to"]):
        detected_primitives["PROCESS_ISOLATION"] = "Worker agent delegation -> Bound via fork()/waitpid() arena GC"

    # 4. EBNF_GRAMMAR
    if "EBNF_GRAMMAR" in finding_ids:
        detected_primitives["EBNF_GRAMMAR"] = "Output format constraints / pause-tool gating conflict"
    elif any(k in lines_lower for k in ["json only", "format strictly", "pause gate", "wait for user", "stop and ask before"]):
        detected_primitives["EBNF_GRAMMAR"] = "Unconstrained response grammar -> Enforce hard XOR mutual exclusion"

    # 5. DESIGN_BY_CONTRACT
    if "DESIGN_BY_CONTRACT" in finding_ids:
        detected_primitives["DESIGN_BY_CONTRACT"] = "Informal testing / edge-case pleading"
    elif any(k in lines_lower for k in ["unit test", "edge case", "acceptance criteria", "invariants", "precondition", "postcondition"]):
        detected_primitives["DESIGN_BY_CONTRACT"] = "Informal test criteria -> Formalize with @requires/@ensures and QuickCheck laws"

    # 6. TWO_PHASE_COMMIT
    if "TWO_PHASE_COMMIT" in finding_ids:
        detected_primitives["TWO_PHASE_COMMIT"] = "Cross-module refactoring without atomicity guarantees"
    elif any(k in lines_lower for k in ["refactor across", "atomic change", "all or nothing", "multi-file refactor"]):
        detected_primitives["TWO_PHASE_COMMIT"] = "Multi-file mutations -> Enforce WAL + 2PC (PREPARE -> COMMIT/ROLLBACK)"

    # 7. CIRCUIT_BREAKER
    if "CIRCUIT_BREAKER" in finding_ids:
        detected_primitives["CIRCUIT_BREAKER"] = "Unbounded retry loop / apology death spiral"
    elif any(k in lines_lower for k in ["retry until", "if failed try again", "when stuck", "repeat on failure"]):
        detected_primitives["CIRCUIT_BREAKER"] = "Retry loops -> Trip to OPEN at k=2 repeated failures with hard halt"

    # 8. GIT_BISECT
    if "GIT_BISECT" in finding_ids:
        detected_primitives["GIT_BISECT"] = "Linear guesswork debugging / regression tracing"
    elif any(k in lines_lower for k in ["binary search", "git bisect", "find regression", "figure out what broke", "root cause"]):
        detected_primitives["GIT_BISECT"] = "Ad-hoc debugging -> Logarithmic binary partitioning O(log2 N)"

    # 9. LKML_PATCH_SERIES
    if "LKML_PATCH_SERIES" in finding_ids:
        detected_primitives["LKML_PATCH_SERIES"] = "Vague commit decomposition / Conventional Commits guidelines"
    elif any(k in lines_lower for k in ["clean commit", "logical commit", "commit message convention", "patch series"]):
        detected_primitives["LKML_PATCH_SERIES"] = "Commit structuring -> LKML [PATCH 0/N] series with git rebase --exec invariant"

    # 10. COMPILER_DIAGNOSTICS
    if "COMPILER_DIAGNOSTICS" in finding_ids:
        detected_primitives["COMPILER_DIAGNOSTICS"] = "Polite / superficial code review checklist"
    elif any(k in lines_lower for k in ["code review", "review the diff", "check for bugs", "code quality checklist"]):
        detected_primitives["COMPILER_DIAGNOSTICS"] = "Code review -> Multi-pass compiler diagnostics (error[SCAR-XX])"

    # 11. STREAM_DEMUX
    if "STREAM_DEMUX" in finding_ids:
        detected_primitives["STREAM_DEMUX"] = "Mixed payload and conversational prose in single channel"
    elif any(k in lines_lower for k in ["stdout", "stderr", "mix data", "payload and comments", "no conversational text"]):
        detected_primitives["STREAM_DEMUX"] = "Channel mixing -> POSIX stream demux (FD 1 pure payload vs FD 2 diagnostics)"

    # 12. POSIX_SIGNALS
    if "POSIX_SIGNALS" in finding_ids:
        detected_primitives["POSIX_SIGNALS"] = "Unstructured cancellation / teardown handling"
    elif any(k in lines_lower for k in ["sigint", "sigterm", "cancellation", "graceful shutdown", "clean exit"]):
        detected_primitives["POSIX_SIGNALS"] = "Interruption handling -> POSIX signal traps (SIGINT checkpoint, SIGTERM rollback)"

    # 13. FILE_LOCKING
    if "FILE_LOCKING" in finding_ids:
        detected_primitives["FILE_LOCKING"] = "Unsynchronized concurrent agent writes"
    elif any(k in lines_lower for k in ["concurrent write", "race condition", "file lock", "flock"]):
        detected_primitives["FILE_LOCKING"] = "Concurrent mutations -> Advisory file locking (flock(2) / <file>.lock)"

    # 14. FAIL_FAST_SHELL
    if "FAIL_FAST_SHELL" in finding_ids:
        detected_primitives["FAIL_FAST_SHELL"] = "Permissive silent script error swallowing"
    elif any(k in lines_lower for k in ["set -e", "pipefail", "fail-fast", "stop on error"]):
        detected_primitives["FAIL_FAST_SHELL"] = "Script execution -> set -euo pipefail fail-fast invariant"

    # 15. SPECULATIVE_COW
    if "SPECULATIVE_COW" in finding_ids:
        detected_primitives["SPECULATIVE_COW"] = "Unhedged in-place speculative trial edits"
    elif any(k in lines_lower for k in ["scratch worktree", "git worktree", "speculative edit", "undo if failed"]):
        detected_primitives["SPECULATIVE_COW"] = "Trial modifications -> Copy-On-Write scratch worktrees (git worktree)"

    # 16. LEAST_PRIVILEGE
    if "LEAST_PRIVILEGE" in finding_ids:
        detected_primitives["LEAST_PRIVILEGE"] = "Conversational pleading for read-only / tool restrictions"
    elif any(k in lines_lower for k in ["read-only mode", "do not modify files", "forbidden to edit", "least privilege"]):
        detected_primitives["LEAST_PRIVILEGE"] = "Tool restrictions -> Principle of Least Privilege / Capabilities (chmod r--)"

    # 17. RING_BUFFER
    if "RING_BUFFER" in finding_ids:
        detected_primitives["RING_BUFFER"] = "Unbounded log output / terminal context flooding"
    elif any(k in lines_lower for k in ["ring buffer", "logrotate", "truncate log", "tail output", "save tokens"]):
        detected_primitives["RING_BUFFER"] = "Terminal logs -> Circular Ring Buffer (head 5 + tail 45 lines, O(1) bound)"

    # Map detected primitives into subsystems
    subsystem_matches: Dict[str, List[Dict]] = {}
    for pid, reason in detected_primitives.items():
        sub = PRIMITIVE_SUBSYSTEM_MAP.get(pid)
        if sub:
            sub_id = sub["id"]
            if sub_id not in subsystem_matches:
                subsystem_matches[sub_id] = []
            pat = PRIMITIVE_MAP.get(pid, {})
            subsystem_matches[sub_id].append({
                "primitive_id": pid,
                "name": pat.get("name", pid),
                "canonical": pat.get("canonical", pid),
                "reason": reason,
                "explanation": pat.get("explanation", ""),
                "snippet": pat.get("snippet", "")
            })

    is_reference = len(detected_primitives) == 0 and len(findings) == 0

    return {
        "rel_path": rel_path,
        "detected_primitives": detected_primitives,
        "subsystem_matches": subsystem_matches,
        "is_reference": is_reference,
    }

def format_scan_report(filepath: str, findings: List[Dict], total_lines: int, content: str = "") -> str:
    score = calculate_friction_score(findings, total_lines)
    status = "CRITICAL: Highly Fragile" if score > 60 else "MODERATE: Can be hardened" if score > 20 else "LOW: Minor friction detected" if score > 0 else "CLEAN: Aligns with canonical CS primitives"
    rel_path = os.path.basename(filepath)
    suit = classify_file_suitability(content, rel_path, findings)

    lines = [
        f"=== Pre-Training Friction Analysis ===",
        f"Target: {filepath}",
        f"Total Lines: {total_lines}",
        f"Friction Score: {score}/100 ({status})",
        f"Fragile Anti-Patterns Found: {len(findings)}\n"
    ]
    
    if findings:
        for idx, f in enumerate(findings, 1):
            p = f["pattern"]
            lines.append(f"[{idx}] {p['name']} (ID: {p['id']})")
            lines.append(f"    Detected matches: {len(f['matches'])}")
            for m in f["matches"][:3]:
                snippet = m.strip().replace("\n", " ")
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."
                lines.append(f"      - \"{snippet}\"")
            lines.append(f"    Mapped Canonical CS Primitive:")
            lines.append(f"      -> {p['canonical']}")
            lines.append(f"    Rationale: {p['explanation']}")
            lines.append(f"    Suggested Template:")
            for s_line in p["snippet"].strip().split("\n"):
                lines.append(f"        {s_line}")
            lines.append("")
    else:
        lines.append("No direct syntactic anti-patterns detected in lexical scan.")
        lines.append("Evaluating architectural suitability from document structure...\n")

    lines.append("=== Canonical Unix & CS Primitives Architecture Audit (7 Subsystems / 17 Primitives) ===")
    lines.append("")

    if suit["subsystem_matches"]:
        lines.append("* Matched OS Subsystems & Canonical Primitives:")
        for sub in SUBSYSTEMS:
            sub_id = sub["id"]
            if sub_id in suit["subsystem_matches"]:
                matches = suit["subsystem_matches"][sub_id]
                lines.append(f"  [{sub['num']}/7] {sub['name']} ({sub['canonical']}):")
                for m in matches:
                    lines.append(f"    - {m['canonical']} (ID: {m['primitive_id']}):")
                    lines.append(f"        Trigger: {m['reason']}")
                    lines.append(f"        Invariant: {m['explanation']}")
        lines.append("")
    else:
        lines.append("* Matched OS Subsystems: None (No procedural anti-patterns detected)")
        lines.append("")

    lines.append("* Domain Reference & Invariants:")
    if suit["is_reference"]:
        lines.append("  - Pure domain documentation & repo guidelines. Preserve as markdown reference.")
    else:
        lines.append("  - Project architecture, technology stack, and domain business rules remain as markdown context.")
    lines.append("")

    lines.append("=== Actionable Recommendations ===")
    if suit["detected_primitives"] or findings:
        lines.append(f"1. Refactor file non-destructively into canonical CS formalisms:")
        lines.append(f"   -> /unix-primitives convert {filepath}")
    else:
        lines.append(f"1. File is already well-structured or serves as reference documentation.")

    lines.append(f"2. Initialize physical disk state runtime (.state/) to survive context compaction:")
    lines.append(f"   -> /unix-init <ticket-id> \"<task-title>\"")

    return "\n".join(lines)

def is_global_path(path: str) -> bool:
    abs_p = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
    home = os.path.realpath(os.path.expanduser("~"))
    global_indicators = [
        os.path.join(home, ".gemini"),
        os.path.join(home, ".config"),
        os.path.join(home, ".agents"),
    ]
    for ind in global_indicators:
        if abs_p == ind or abs_p.startswith(ind + os.sep):
            return True
    return False

def collect_agent_files(dir_path: str) -> List[str]:
    valid_exts = {".md", ".yaml", ".yml", ".txt"}
    collected = []
    skip_dirs = {".git", "node_modules", ".state", "archive", "__pycache__"}
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            if f.startswith("."):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                collected.append(os.path.join(root, f))
    return sorted(collected)

def scan_directory(dir_path: str) -> None:
    if is_global_path(dir_path):
        print(f"Error: Refusing to scan global configuration directory: {dir_path}", file=sys.stderr)
        print("Folder scanning is strictly restricted to local workspace .agents/ directories.", file=sys.stderr)
        sys.exit(1)

    files = collect_agent_files(dir_path)
    if not files:
        print(f"No scanable rules, skills, or workflows found in: {dir_path}")
        return

    file_results = []
    total_findings_count = 0
    total_lines_count = 0

    for fpath in files:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        lines = len(content.splitlines())
        findings = scan_text(content)
        score = calculate_friction_score(findings, lines)
        total_findings_count += len(findings)
        total_lines_count += lines
        rel_path = os.path.relpath(fpath, os.path.dirname(dir_path))
        suit = classify_file_suitability(content, rel_path, findings)
        file_results.append({
            "path": fpath,
            "rel_path": rel_path,
            "lines": lines,
            "score": score,
            "findings": findings,
            "suit": suit
        })

    avg_score = sum(r["score"] for r in file_results) // len(file_results) if file_results else 0
    max_score = max((r["score"] for r in file_results), default=0)
    status = "CRITICAL: Highly Fragile" if max_score > 60 else "MODERATE: Can be hardened" if max_score > 20 else "LOW: Minor friction detected" if max_score > 0 else "CLEAN: Aligns with canonical CS primitives"

    print("=== Local .agents/ Workspace Friction Audit ===")
    print(f"Target Directory: {dir_path}")
    print(f"Scanned Files: {len(file_results)} files ({total_lines_count} total lines)")
    print(f"Total Anti-Patterns Detected: {total_findings_count}")
    print(f"Project Health: {status} (Average Score: {avg_score}/100, Peak Friction: {max_score}/100)\n")

    print(f"{'Score':<8} | {'Lines':<6} | {'File':<40} | {'Primary Subsystem'}")
    print("-" * 80)
    for r in file_results:
        if r["suit"]["subsystem_matches"]:
            first_sub_id = next(iter(r["suit"]["subsystem_matches"]))
            sub_name = next((s["name"] for s in SUBSYSTEMS if s["id"] == first_sub_id), "Active")
        elif r["findings"]:
            sub_name = r["findings"][0]["pattern"]["id"]
        else:
            sub_name = "Domain Reference"
        print(f"{r['score']:<3}/100  | {r['lines']:<6} | {r['rel_path'][:40]:<40} | {sub_name[:24]}")

    needy_files = [r for r in file_results if r["score"] > 20]
    if needy_files:
        print("\n--- High-Friction Files Requiring Hardening ---")
        for r in needy_files:
            print(f"\nTarget: {r['rel_path']} (Score: {r['score']}/100)")
            for f_idx, f in enumerate(r["findings"][:3], 1):
                p = f["pattern"]
                print(f"  [{f_idx}] {p['name']} -> Use {p['canonical']}")

    # Canonical Architecture Audit: 7 OS Subsystems
    print("\n=== Canonical Architecture Audit: 7 OS Subsystems (17 Formalisms) ===")
    for sub in SUBSYSTEMS:
        sub_id = sub["id"]
        matching_files = [r for r in file_results if sub_id in r["suit"]["subsystem_matches"]]
        print(f"\n[{sub['num']}/7] {sub['name']} ({sub['canonical']}):")
        if matching_files:
            for r in matching_files:
                reasons = [m["reason"] for m in r["suit"]["subsystem_matches"][sub_id]]
                print(f"  - {r['rel_path']}: {'; '.join(reasons)}")
        else:
            print("  - None detected")

    ref_files = [r for r in file_results if r["suit"]["is_reference"]]
    print("\n[Domain Reference & Invariants]:")
    if ref_files:
        for r in ref_files:
            print(f"  - {r['rel_path']}: Domain context / guidelines. Preserve as markdown reference.")
    else:
        print("  - All scanned files contain active behavioral or workflow invariants.")

    print("\n=== Actionable Recommendations ===")
    step_num = 1
    high_friction = [r for r in file_results if r["score"] > 20 or r["suit"]["detected_primitives"]]
    if high_friction:
        top_target = high_friction[0]
        print(f"{step_num}. Refactor high-friction file into canonical CS formalisms:")
        print(f"   -> /unix-primitives convert {top_target['rel_path']}")
        step_num += 1
    print(f"{step_num}. Initialize physical disk state runtime (.state/) in workspace:")
    print(f"   -> /unix-init <ticket-id> \"<title>\"")

def get_next_increment_path(target_path: str) -> str:
    dir_name = os.path.dirname(os.path.abspath(target_path))
    base_name = os.path.basename(target_path)
    if "." in base_name and not base_name.startswith("."):
        stem, ext = base_name.rsplit(".", 1)
        ext = f".{ext}"
    else:
        stem, ext = base_name, ""

    pattern = re.compile(rf"^{re.escape(stem)}\.(\d{{2}}){re.escape(ext)}$")
    existing_nums = []
    if os.path.exists(dir_name):
        for fname in os.listdir(dir_name):
            m = pattern.match(fname)
            if m:
                existing_nums.append(int(m.group(1)))

    next_num = max(existing_nums, default=0) + 1
    return os.path.join(dir_name, f"{stem}.{next_num:02d}{ext}")

def auto_detect_target() -> Optional[str]:
    # 1. Local .agents directory
    if os.path.isdir(".agents"):
        return ".agents"
    # 2. Common prompt/agent guideline files
    common_candidates = [
        "CLAUDE.md",
        ".cursorrules",
        "CONVENTIONS.md",
        "AGENTS.md",
        "SYSTEM_PROMPT.md",
        "README.md",
    ]
    for candidate in common_candidates:
        if os.path.isfile(candidate):
            return candidate
    # 3. Any markdown file in current root directory
    try:
        md_files = sorted([f for f in os.listdir(".") if f.endswith(".md") and os.path.isfile(f) and not f.startswith(".")])
        if md_files:
            return md_files[0]
    except Exception:
        pass
    return None

def generate_subagent_prompt(target_path: str) -> str:
    # Collect target files
    if os.path.isdir(target_path):
        files = collect_agent_files(target_path)
    else:
        files = [target_path]

    telemetry_lines = []
    telemetry_lines.append(f"Target: {target_path} ({len(files)} files)")
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                fc = fp.read()
            lines = len(fc.splitlines())
            fnds = scan_text(fc)
            score = calculate_friction_score(fnds, lines)
            rel = os.path.relpath(f, os.path.dirname(target_path) if os.path.isdir(target_path) else os.path.dirname(f))
            top = fnds[0]["pattern"]["id"] if fnds else "CLEAN"
            telemetry_lines.append(f"- `{rel}`: {lines} lines, score {score}/100, top finding: {top}")
        except Exception:
            telemetry_lines.append(f"- `{f}`: (unable to read)")

    prompt = f"""Role: Prompt Architecture Auditor
Goal: Semantically audit target prompt/rule files and classify them across the 7 OS Subsystems and 17 Canonical Unix & CS Primitives.

=== TARGET INVENTORY & TELEMETRY ===
{chr(10).join(telemetry_lines)}

=== CANONICAL CLASSIFICATION CONTRACT (7 OS SUBSYSTEMS / 17 PRIMITIVES) ===
[1] Build & Execution DAGs:
    * MAKEFILE_DAG (1): Sequential checklists, workflows, build/test chains. Invariant: Backward-chaining DAG + mtime invalidation.

[2] State Persistence & Lifecycle:
    * SYSV_INITD (2): Progress tracking, mutable todos, amnesia. Invariant: Externalized disk latches 00_ to 99_ + RFC 822 headers survive 200k+ compaction.
    * POSIX_SIGNALS (12): Cancellation, teardown, interruption. Invariant: SIGINT checkpoint, SIGTERM rollback, SIGHUP reload traps.

[3] Process Isolation & Concurrency:
    * PROCESS_ISOLATION (3): Subagent delegation, unbounded context. Invariant: fork()/waitpid(), arena GC on exit 0, orchestrator <30k tokens.
    * FILE_LOCKING (13): Concurrent agent writes, collisions. Invariant: Advisory lock flock(2) / <file>.lock mutual exclusion.
    * LEAST_PRIVILEGE (16): Pleading not to touch files. Invariant: Principle of Least Privilege / Capabilities (chmod r--).

[4] Protocols & Stream Demux:
    * EBNF_GRAMMAR (4): Output formatting, pause gates. Invariant: RFC 5234 production rules with strict XOR mutual exclusion between pause gate & tools.
    * STREAM_DEMUX (11): Mixed JSON payload & human comments. Invariant: POSIX stream demux (stdout FD 1 pure payload vs stderr FD 2 diagnostics).
    * RING_BUFFER (17): Unbounded terminal logs, context flooding. Invariant: Circular ring buffer FIFO (head 5 + tail 45 lines, O(1) bound).

[5] Verification & Diagnostics:
    * DESIGN_BY_CONTRACT (5): Vague edge-case testing. Invariant: Design-by-Contract (@requires/@ensures/@invariant) + QuickCheck algebraic laws.
    * COMPILER_DIAGNOSTICS (10): Polite code reviews. Invariant: Multi-pass compiler diagnostics (error[SCAR-XX] AST/lifetime/blast-radius passes).

[6] Transaction Safety & Fault Tolerance:
    * TWO_PHASE_COMMIT (6): Multi-file/package refactoring. Invariant: Database WAL + 2PC (PREPARE -> COMMIT/ROLLBACK), zero partial edits.
    * CIRCUIT_BREAKER (7): Apology loops, retries. Invariant: Distributed Circuit Breaker FSM (CLOSED -> OPEN at k=2 repeated errors) + Idempotency keys.
    * FAIL_FAST_SHELL (14): Silent command failures. Invariant: set -euo pipefail zero-tolerance error propagation.
    * SPECULATIVE_COW (15): In-place speculative edits. Invariant: Ephemeral git worktree scratch sandbox, fast-forward merge only if green.

[7] Search & Commit Topology:
    * GIT_BISECT (8): Guess-based debugging. Invariant: Logarithmic binary partitioning O(log2 N).
    * LKML_PATCH_SERIES (9): Commit decomposition. Invariant: LKML [PATCH 0/N] series, git rebase --exec "make test" invariant on every patch.

[Domain Reference & Invariants]:
    * Pure tech stack definitions, domain business rules, and architecture references. Preserve as markdown reference.

=== INSTRUCTIONS ===
1. Use view_file to inspect files in the inventory.
2. Produce a concise audit report grouped by the 7 OS Subsystems (+ Domain Reference).
3. Provide exact Actionable Recommendations (/unix-primitives convert <file> and /unix-init).
4. Full reference catalog: skills/unix-primitives/references/rosetta_stone.md
"""
    return prompt

def format_score_delta(original_path: str, rewritten_path: str) -> str:
    orig_abs = os.path.abspath(os.path.expanduser(original_path))
    rewr_abs = os.path.abspath(os.path.expanduser(rewritten_path))

    if not os.path.isfile(orig_abs):
        return f"Error: Original file not found: {original_path}"
    if not os.path.isfile(rewr_abs):
        return f"Error: Rewritten file not found: {rewritten_path}"

    with open(orig_abs, "r", encoding="utf-8", errors="ignore") as f:
        orig_content = f.read()
    with open(rewr_abs, "r", encoding="utf-8", errors="ignore") as f:
        rewr_content = f.read()

    orig_lines = len(orig_content.splitlines())
    rewr_lines = len(rewr_content.splitlines())

    orig_findings = scan_text(orig_content)
    rewr_findings = scan_text(rewr_content)

    orig_score = calculate_friction_score(orig_findings, orig_lines)
    rewr_score = calculate_friction_score(rewr_findings, rewr_lines)

    orig_primitives = {f["pattern"]["id"]: f["pattern"].get("canonical", f["pattern"]["id"]) for f in orig_findings}
    rewr_primitives = {f["pattern"]["id"]: f["pattern"].get("canonical", f["pattern"]["id"]) for f in rewr_findings}

    resolved_ids = sorted(list(set(orig_primitives.keys()) - set(rewr_primitives.keys())))
    remaining_ids = sorted(list(set(rewr_primitives.keys())))
    new_ids = sorted(list(set(rewr_primitives.keys()) - set(orig_primitives.keys())))

    delta = rewr_score - orig_score
    pct_reduction = 0.0
    if orig_score > 0:
        pct_reduction = ((orig_score - rewr_score) / orig_score) * 100.0

    lines = [
        "=== Pre-Training Friction Score Delta ===",
        f"Original:  {original_path} ({orig_lines} lines)",
        f"           -> Score: {orig_score}/100 ({len(orig_findings)} anti-pattern matches)",
        f"Rewritten: {rewritten_path} ({rewr_lines} lines)",
        f"           -> Score: {rewr_score}/100 ({len(rewr_findings)} anti-pattern matches)",
        "",
        f"Delta:     {delta:+d} ({pct_reduction:.1f}% friction reduction)" if orig_score > 0 else f"Delta:     {delta:+d}",
    ]

    if resolved_ids:
        resolved_str = ", ".join(f"{pid} ({orig_primitives[pid]})" for pid in resolved_ids)
        lines.append(f"Resolved:  {resolved_str}")
    else:
        lines.append("Resolved:  None")

    if remaining_ids:
        rem_str = ", ".join(f"{pid} ({rewr_primitives[pid]})" for pid in remaining_ids)
        lines.append(f"Remaining: {rem_str}")
    else:
        lines.append("Remaining: NONE (Clean - zero anti-pattern matches)")

    if new_ids:
        new_str = ", ".join(f"{pid} ({rewr_primitives[pid]})" for pid in new_ids)
        lines.append(f"Introduced: {new_str}")

    return "\n".join(lines)

def main():
    # If first argument is a file/path rather than a subcommand, default to 'scan'
    known_cmds = {"scan", "convert", "rewrite", "audit-prompt", "delta"}
    if len(sys.argv) > 1 and sys.argv[1] not in known_cmds and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "scan")

    parser = argparse.ArgumentParser(description="Analyze or refactor prompts into canonical Unix & CS primitives.")
    subparsers = parser.add_subparsers(dest="command")

    # scan (supports single file or local .agents folder)
    p_scan = subparsers.add_parser("scan", help="Scan file or local .agents/ folder for friction report (default)")
    p_scan.add_argument("target", nargs="?", help="Path to file or local .agents/ directory (defaults to auto-detection)")

    # delta (compare original vs rewritten score)
    p_delta = subparsers.add_parser("delta", help="Compute friction score delta between original and rewritten file")
    p_delta.add_argument("original", help="Path to original file")
    p_delta.add_argument("rewritten", help="Path to rewritten file")

    # audit-prompt (generate full non-paraphrased subagent audit prompt)
    p_audit = subparsers.add_parser("audit-prompt", help="Generate full non-paraphrased subagent audit prompt bundle")
    p_audit.add_argument("target", nargs="?", help="Path to file or local .agents/ directory")
    p_audit.add_argument("--save-to", help="Optional file path to save the generated prompt")

    # convert (default non-destructive, writes to <target>.NN.md)
    p_convert = subparsers.add_parser("convert", help="Convert non-destructively to <target>.NN.md")
    p_convert.add_argument("target", help="Path to target file")
    p_convert.add_argument("--output", help="Custom output path")

    # rewrite (in-place rewrite with <target>.original.md backup)
    p_rewrite = subparsers.add_parser("rewrite", help="Rewrite file in-place with <target>.original.md backup")
    p_rewrite.add_argument("target", help="Path to target file")

    args = parser.parse_args()

    cmd = args.command

    if cmd == "delta":
        report = format_score_delta(args.original, args.rewritten)
        print(report)
        sys.exit(0)

    target = getattr(args, "target", None)

    if not cmd or (cmd == "scan" and not target):
        cmd = "scan"
        target = auto_detect_target()
        if not target:
            print("Error: No target specified and no prompt files detected (.agents/, CLAUDE.md, README.md).", file=sys.stderr)
            print("Usage: unix_primitives.py [scan|convert|rewrite|audit-prompt|delta] <target>", file=sys.stderr)
            sys.exit(1)
        print(f"No target specified. Defaulting to 'scan {target}'...\n")

    target_path = os.path.abspath(os.path.expanduser(target))
    if not os.path.exists(target_path):
        print(f"Error: Target path not found: {target_path}", file=sys.stderr)
        sys.exit(1)

    if cmd == "audit-prompt":
        prompt = generate_subagent_prompt(target_path)
        out_save = getattr(args, "save_to", None)
        if out_save:
            with open(out_save, "w", encoding="utf-8") as out_fp:
                out_fp.write(prompt)
            print(f"Generated subagent audit prompt written to: {out_save}")
        else:
            print(prompt)
        sys.exit(0)

    # Check if directory
    if os.path.isdir(target_path):
        if cmd in ("scan", None):
            scan_directory(target_path)
            sys.exit(0)
        else:
            print(f"Error: Command '{cmd}' requires a single file target, not a directory: {target_path}", file=sys.stderr)
            sys.exit(1)

    # Single file processing
    with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    total_lines = len(content.splitlines())
    findings = scan_text(content)
    report = format_scan_report(target_path, findings, total_lines, content)
    print(report)

    if cmd == "convert":
        out_path = getattr(args, "output", None) or get_next_increment_path(target_path)
        print(f"=== Non-Destructive Conversion Target ===")
        print(f"Destination: {out_path}")
        print(f"Original file remains untouched: {target_path}")
    elif cmd == "rewrite":
        backup_path = f"{target_path}.original.md"
        print(f"=== In-Place Rewrite Target ===")
        print(f"Target: {target_path}")
        print(f"Backup destination: {backup_path}")

if __name__ == "__main__":
    main()


