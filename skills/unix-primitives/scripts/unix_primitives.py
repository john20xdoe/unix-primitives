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
        "regex": r"(?i)(step\s*\d+.*(?:then|go\s*to\s*step|return\s*to\s*step)|1\.\s+First.*2\.\s+Second.*3\.\s+Third)",
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
        "regex": r"(?i)(keep\s+a\s+(?:progress|todo)\.md|update\s+(?:progress|todo)\.md|track\s+steps\s+in\s+markdown)",
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
        "regex": r"(?i)(spawn\s+a\s+subagent\s+when\s+needed|subagents?\s+to\s+explore.*clean\s+up)",
        "canonical": "Unix Process Control (fork() / waitpid() / trap EXIT)",
        "explanation": "Treat process boundaries as arena garbage collectors. Retain compact orchestrator context (<30k tokens).",
        "snippet": """PID 1 (Orchestrator): fork(role="Archaeology") -> waitpid()
Child: trap 'rm -rf /tmp/scratch_$$' EXIT -> write disk artifact -> exit 0"""
    },
    {
        "id": "EBNF_GRAMMAR",
        "name": "Unconstrained Response Output / Gate Conflict",
        "regex": r"(?i)(format\s+your\s+output\s+strictly|never\s+call\s+a\s+tool\s+if\s+asking|do\s+not\s+emit\s+tools?\s+while\s+pausing)",
        "canonical": "RFC 5234 EBNF Grammar (Strict Mutual Exclusion)",
        "explanation": "Constrain turn response structure using production rules with hard XOR exclusivity.",
        "snippet": """turn_response ::= status_header "\\n\\n" (tool_action | pause_gate)
(* Invariant: tool_action and pause_gate are strictly mutually exclusive *)"""
    },
    {
        "id": "DESIGN_BY_CONTRACT",
        "name": "Sunny-Day / Vague Test Prompting",
        "regex": r"(?i)(write\s+unit\s+tests.*(?:cover\s+edge\s+cases|handle\s+errors)|ensure\s+edge\s+cases\s+are\s+tested)",
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
        "regex": r"(?i)(refactor\s+across\s+packages.*don'?t\s+leave\s+broken|update\s+all\s+files.*without\s+breaking)",
        "canonical": "Database WAL + Two-Phase Commit (2PC: PREPARE -> COMMIT/ROLLBACK)",
        "explanation": "Enforce atomic cross-package mutations. Commit iff all participants vote PREPARED, else full ROLLBACK.",
        "snippet": """PHASE 1 (PREPARE): Verify scratch worktree per participant
PHASE 2 (DECIDE): If all PREPARED -> COMMIT, else ROLLBACK"""
    },
    {
        "id": "CIRCUIT_BREAKER",
        "name": "Apology Death Spiral / Unbounded Retries",
        "regex": r"(?i)(if\s+(?:it|tests?)\s+fails?,?\s+try\s+(?:again|a\s+couple\s+times|to\s+fix)|retry\s+until\s+working)",
        "canonical": "Distributed Circuit Breaker FSM (CLOSED -> OPEN) + Idempotency Keys",
        "explanation": "Halt repetitive retry loops after k=2 failures. Trip to OPEN state and escalate immediately.",
        "snippet": """threshold: k=2
If failures >= 2: STATE = OPEN -> HARD HALT. Suppress retry. Escalate to human."""
    },
    {
        "id": "GIT_BISECT",
        "name": "Linear Flailing / Guess-Based Debugging",
        "regex": r"(?i)(figure\s+out\s+why\s+(?:this|the)\s+test\s+is\s+failing|find\s+which\s+commit\s+broke)",
        "canonical": "git bisect (Logarithmic Binary Search O(log2 N))",
        "explanation": "Partition causal search space into binary halves using midpoint probes rather than linear scans.",
        "snippet": """mid = (low + high) // 2
Probe mid -> adjust bounds -> converge in ceil(log2 N) steps."""
    },
    {
        "id": "LKML_PATCH_SERIES",
        "name": "Vague Commit Decomposition",
        "regex": r"(?i)(break\s+changes\s+into\s+clean\s+commits|make\s+logical\s+commits)",
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
        "regex": r"(?i)(review\s+code\s+carefully|check\s+code\s+for\s+bugs\s+before\s+submitting)",
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
        "regex": r"(?i)(output\s+json.*(?:feel\s+free\s+to\s+explain|add\s+your\s+thoughts)|mix\s+(?:data|json)\s+with\s+(?:text|comments))",
        "canonical": "POSIX Stream Demux (stdout FD 1 vs stderr FD 2)",
        "explanation": "Strictly segregate machine-parsable payloads (stdout) from diagnostic notes (stderr).",
        "snippet": """stdout (FD 1): Pure payload (raw JSON / diff / AST).
stderr (FD 2): Diagnostic progress & human notes.
exit code: 0 on success, >0 on failure."""
    },
    {
        "id": "POSIX_SIGNALS",
        "name": "Vague Teardown / Interruption Handling",
        "regex": r"(?i)(if\s+user\s+(?:cancels|stops|interrupts).*finish\s+(?:up\s+nicely|cleanly)|handle\s+cancellation\s+gracefully)",
        "canonical": "POSIX Signal Handlers (SIGINT, SIGTERM, SIGHUP)",
        "explanation": "Bind interruptions to deterministic signal traps: SIGINT (checkpoint), SIGTERM (rollback & clean exit).",
        "snippet": """SIGINT  -> trap checkpoint_and_pause: flush state to `99_next_action.md`
SIGTERM -> trap rollback_and_exit: rollback uncommitted WAL, exit 0"""
    },
    {
        "id": "FILE_LOCKING",
        "name": "Unsynchronized Concurrent Agent Writes",
        "regex": r"(?i)(make\s+sure\s+(?:subagents|agents)\s+don'?t\s+overwrite|avoid\s+conflicting\s+edits\s+between\s+agents)",
        "canonical": "Advisory File Locking (flock(2) / <file>.lock)",
        "explanation": "Enforce atomic lockfile acquisition before mutating files across concurrent subagents.",
        "snippet": """acquire_lock("<file>.lock", timeout_ms=3000)
# mutate file
release_lock("<file>.lock")"""
    },
    {
        "id": "FAIL_FAST_SHELL",
        "name": "Permissive / Silent Command Error Swallowing",
        "regex": r"(?i)(run\s+these\s+commands.*if\s+anything\s+fails\s+stop|execute\s+steps\s+and\s+abort\s+on\s+error)",
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
        "regex": r"(?i)(try\s+editing\s+to\s+see\s+if\s+it\s+works.*undo\s+if\s+fails|speculative\s+change.*revert\s+if)",
        "canonical": "Copy-On-Write Scratch Worktrees (git worktree)",
        "explanation": "Isolate experimental mutations in ephemeral git worktree; fast-forward merge only on test pass.",
        "snippet": """git worktree add -b scratch/tx ../scratch-tx HEAD
# test passes -> fast-forward merge
# test fails -> git worktree remove --force ../scratch-tx"""
    },
    {
        "id": "LEAST_PRIVILEGE",
        "name": "Vague Role-Based Behavioral Pleading",
        "regex": r"(?i)(you\s+are\s+an\s+explorer.*only\s+look.*don'?t\s+(?:touch|modify)|read-only\s+mode.*don'?t\s+change)",
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
        "regex": r"(?i)(don'?t\s+print\s+too\s+much\s+log|limit\s+log\s+output\s+to\s+save\s+tokens|avoid\s+long\s+terminal\s+dumps)",
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

def calculate_friction_score(findings: List[Dict], total_lines: int) -> int:
    if not findings:
        return 0
    raw_score = sum(len(f["matches"]) * 15 for f in findings)
    return min(100, max(15, raw_score))

def format_scan_report(filepath: str, findings: List[Dict], total_lines: int) -> str:
    score = calculate_friction_score(findings, total_lines)
    status = "CRITICAL: Highly Fragile" if score > 60 else "MODERATE: Can be hardened" if score > 20 else "CLEAN"
    lines = [
        f"=== Pre-Training Friction Analysis ===",
        f"Target: {filepath}",
        f"Total Lines: {total_lines}",
        f"Friction Score: {score}/100 ({status})",
        f"Fragile Anti-Patterns Found: {len(findings)}\n"
    ]
    
    if not findings:
        lines.append("No fragile prompt anti-patterns detected. File aligns well with canonical CS primitives.")
        return "\n".join(lines)
        
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
        file_results.append({
            "path": fpath,
            "rel_path": rel_path,
            "lines": lines,
            "score": score,
            "findings": findings
        })

    avg_score = sum(r["score"] for r in file_results) // len(file_results) if file_results else 0
    max_score = max((r["score"] for r in file_results), default=0)
    status = "CRITICAL: Highly Fragile" if max_score > 60 else "MODERATE: Can be hardened" if max_score > 20 else "CLEAN"

    print("=== Local .agents/ Workspace Friction Audit ===")
    print(f"Target Directory: {dir_path}")
    print(f"Scanned Files: {len(file_results)} files ({total_lines_count} total lines)")
    print(f"Total Anti-Patterns Detected: {total_findings_count}")
    print(f"Project Health: {status} (Average Score: {avg_score}/100, Peak Friction: {max_score}/100)\n")

    print(f"{'Score':<8} | {'Lines':<6} | {'File':<40} | {'Top Finding'}")
    print("-" * 80)
    for r in file_results:
        top_finding = r["findings"][0]["pattern"]["id"] if r["findings"] else "CLEAN"
        print(f"{r['score']:<3}/100  | {r['lines']:<6} | {r['rel_path'][:40]:<40} | {top_finding}")

    needy_files = [r for r in file_results if r["score"] > 20]
    if needy_files:
        print("\n--- High-Friction Files Requiring Hardening ---")
        for r in needy_files:
            print(f"\nTarget: {r['rel_path']} (Score: {r['score']}/100)")
            for f_idx, f in enumerate(r["findings"][:3], 1):
                p = f["pattern"]
                print(f"  [{f_idx}] {p['name']} -> Use {p['canonical']}")

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

def main():
    # If first argument is a file/path rather than a subcommand, default to 'scan'
    known_cmds = {"scan", "convert", "rewrite"}
    if len(sys.argv) > 1 and sys.argv[1] not in known_cmds and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "scan")

    parser = argparse.ArgumentParser(description="Analyze or refactor prompts into canonical Unix & CS primitives.")
    subparsers = parser.add_subparsers(dest="command")

    # scan (supports single file or local .agents folder)
    p_scan = subparsers.add_parser("scan", help="Scan file or local .agents/ folder for friction report (default)")
    p_scan.add_argument("target", nargs="?", help="Path to file or local .agents/ directory (defaults to auto-detection)")

    # convert (default non-destructive, writes to <target>.NN.md)
    p_convert = subparsers.add_parser("convert", help="Convert non-destructively to <target>.NN.md")
    p_convert.add_argument("target", help="Path to target file")
    p_convert.add_argument("--output", help="Custom output path")

    # rewrite (in-place rewrite with <target>.original.md backup)
    p_rewrite = subparsers.add_parser("rewrite", help="Rewrite file in-place with <target>.original.md backup")
    p_rewrite.add_argument("target", help="Path to target file")

    args = parser.parse_args()

    cmd = args.command
    target = getattr(args, "target", None)

    if not cmd or (cmd == "scan" and not target):
        cmd = "scan"
        target = auto_detect_target()
        if not target:
            print("Error: No target specified and no prompt files detected (.agents/, CLAUDE.md, README.md).", file=sys.stderr)
            print("Usage: unix_primitives.py [scan|convert|rewrite] <target>", file=sys.stderr)
            sys.exit(1)
        print(f"No target specified. Defaulting to 'scan {target}'...\n")

    target_path = os.path.abspath(os.path.expanduser(target))
    if not os.path.exists(target_path):
        print(f"Error: Target path not found: {target_path}", file=sys.stderr)
        sys.exit(1)

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
    report = format_scan_report(target_path, findings, total_lines)
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


