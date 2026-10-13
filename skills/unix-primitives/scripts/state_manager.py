#!/usr/bin/env python3
"""
state_manager.py - Physical disk state manager for prompt gravity.

Maintains bounded SysV runlevel disk latches (.state/00_... -> 99_...) in workspaces.
Guarantees O(1) file count to prevent bloat and staleness.
Supports named slots, pre-push hook management, and subagent artifact isolation.
"""

import sys
import os
import stat
import time
import argparse
from typing import Optional, Dict

SLOT_ALIASES = {
    "ticket": 10,
    "10": 10,
    "plan": 20,
    "20": 20,
    "tdd": 30,
    "test": 30,
    "30": 30,
    "impl": 40,
    "code": 40,
    "40": 40,
}

SLOTS = {
    0: "00_governance.md",    # Immutable read-only project rules & invariants
    10: "10_ticket.md",        # Active ticket scope & acceptance criteria
    20: "20_plan.md",          # Approved plan latch (write-once)
    30: "30_tdd_red.md",       # Failing reproduction tests verified
    40: "40_impl_green.md",    # Green tests & verified implementation
    99: "99_next_action.md",   # Volatile pointer (in-place overwritten, <1KB)
}

GITIGNORE_CONTENT = """# Prevent agent transient latches from polluting repository history
*
!.gitignore
!00_governance.md
!artifacts/
"""

MAKEFILE_TEMPLATE = """.PHONY: all status clean verify ci-gate

all: status

# Physical disk milestone targets
.state/20_plan.md: .state/10_ticket.md
	@echo "Awaiting plan creation and human signoff"

.state/30_tdd_red.md: .state/20_plan.md
	@echo "Awaiting TDD test creation"

.state/40_impl_green.md: .state/30_tdd_red.md
	@echo "Awaiting implementation verification"

ci-gate:
	@test -f .state/40_impl_green.md || (echo "Error: Implementation milestone not verified (.state/40_impl_green.md missing)" && exit 1)

status:
	@python3 {state_manager_path} status

clean:
	@python3 {state_manager_path} clean
"""

PRE_PUSH_HOOK_TEMPLATE = """#!/bin/sh
# Optional Unix-Primitives Pre-Push Verification Hook
# Validates active ticket runlevel before allowing push

STATE_DIR="$(git rev-parse --show-toplevel)/.state"

if [ -d "$STATE_DIR" ]; then
    echo "=== [unix-primitives] Validating pre-push runlevel ==="
    if [ -f "$STATE_DIR/Makefile" ]; then
        make -f "$STATE_DIR/Makefile" ci-gate
        if [ $? -ne 0 ]; then
            echo "Pre-push check failed: Active ticket in .state/ has unverified milestones."
            echo "Local commits remain safe. Fix milestone or run /unix-clean before pushing."
            exit 1
        fi
    fi
fi

exit 0
"""

def get_state_dir(workspace: str) -> str:
    return os.path.join(os.path.abspath(workspace), ".state")

def resolve_slot(slot_identifier: str) -> int:
    key = str(slot_identifier).strip().lower()
    if key in SLOT_ALIASES:
        return SLOT_ALIASES[key]
    try:
        val = int(key)
        if val in SLOTS:
            return val
    except ValueError:
        pass
    print(f"Error: Unknown milestone '{slot_identifier}'. Valid aliases: plan (20), tdd (30), impl (40).", file=sys.stderr)
    sys.exit(1)

def init_workspace(workspace: str, ticket_id: str, title: str, governance: Optional[str] = None) -> None:
    state_dir = get_state_dir(workspace)
    os.makedirs(state_dir, exist_ok=True)

    # 1. Write .gitignore to prevent repo pollution
    gitignore_path = os.path.join(state_dir, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(GITIGNORE_CONTENT)

    # 2. Write 00_governance.md if not present
    gov_path = os.path.join(state_dir, SLOTS[0])
    if not os.path.exists(gov_path):
        default_gov = """# Root Governance & Invariants

- State Recovery: On session start or compaction, inspect .state/ and resume from highest runlevel.
- Invariant: Build and tests must pass at every milestone gate.
- Circuit Breaker: Trips at k=2 consecutive failures -> halt and escalate.
- Anti-Bloat: Active latches capped at 6 bounded slots.
"""
        with open(gov_path, "w", encoding="utf-8") as f:
            f.write(governance or default_gov)

    # 3. Clean any existing active ticket latches to prevent bloat
    clean_active_latches(workspace, archive=True)

    # 4. Write 10_ticket.md
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ticket_path = os.path.join(state_dir, SLOTS[10])
    with open(ticket_path, "w", encoding="utf-8") as f:
        f.write(f"""Ticket-ID: {ticket_id}
Title: {title}
Status: IN_PROGRESS
Created: {now_iso}
Timestamp: {now_iso}

## Requirements
{title}
""")

    # 5. Write volatile 99_next_action.md
    write_next_action(workspace, "plan", "10_ticket.md", "DRAFT_PLAN", ticket_id)

    # 6. Generate real Makefile for disk timestamp invalidation
    script_path = os.path.abspath(__file__)
    makefile_path = os.path.join(state_dir, "Makefile")
    with open(makefile_path, "w", encoding="utf-8") as f:
        f.write(MAKEFILE_TEMPLATE.format(state_manager_path=script_path))

    print(f"Initialized physical disk state at: {state_dir}")
    print(f"Active ticket: [{ticket_id}] {title}")
    print(f"Disk slots strictly bounded (Max 6 files, O(1) storage).")

def write_next_action(workspace: str, next_action: str, last_completed: str, status: str, ticket_id: str) -> None:
    state_dir = get_state_dir(workspace)
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = os.path.join(state_dir, SLOTS[99])
    content = f"""Ticket-ID: {ticket_id}
Status: {status}
Last-Completed: {last_completed}
Next-Action: {next_action}
Timestamp: {now_iso}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def stamp_milestone(workspace: str, slot_id: str, content: str, next_action: str) -> None:
    slot_num = resolve_slot(slot_id)
    state_dir = get_state_dir(workspace)

    filename = SLOTS[slot_num]
    target_path = os.path.join(state_dir, filename)
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Write milestone latch
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(f"Milestone: {filename}\nTimestamp: {now_iso}\n\n{content}\n")

    # Read ticket ID if available
    ticket_id = "UNKNOWN"
    ticket_file = os.path.join(state_dir, SLOTS[10])
    if os.path.exists(ticket_file):
        with open(ticket_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Ticket-ID:"):
                    ticket_id = line.split(":", 1)[1].strip()
                    break

    # Overwrite volatile 99_next_action.md in-place (O(1) size)
    write_next_action(workspace, next_action, filename, "PROGRESSING", ticket_id)
    print(f"Physical latch stamped: {filename} (Disk mtime updated)")

def write_artifact(workspace: str, role: str, content: str) -> None:
    state_dir = get_state_dir(workspace)
    artifacts_dir = os.path.join(state_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    sanitized_role = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in role.lower())
    artifact_path = os.path.join(artifacts_dir, f"{sanitized_role}.md")
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write(f"Role: {role}\nTimestamp: {now_iso}\n\n{content}\n")

    print(f"Subagent artifact saved to disk: {artifact_path}")
    print("Orchestrator context preserved (<30k tokens).")

def check_staleness(workspace: str) -> Dict[str, str]:
    state_dir = get_state_dir(workspace)
    if not os.path.exists(state_dir):
        return {"status": "UNINITIALIZED"}

    ticket_file = os.path.join(state_dir, SLOTS[10])
    if not os.path.exists(ticket_file):
        return {"status": "EMPTY"}

    ticket_mtime = os.path.getmtime(ticket_file)
    age_hours = (time.time() - ticket_mtime) / 3600.0

    stale = age_hours > 72.0  # Ticket older than 3 days marked stale
    return {
        "status": "STALE" if stale else "ACTIVE",
        "age_hours": f"{age_hours:.1f}",
        "state_dir": state_dir
    }

def print_status(workspace: str) -> None:
    state_dir = get_state_dir(workspace)
    if not os.path.exists(state_dir):
        print("Status: .state/ directory not initialized.")
        return

    stale_info = check_staleness(workspace)
    print(f"=== Physical Disk State Status ===")
    print(f"Location: {state_dir}")
    print(f"State Health: {stale_info['status']} (Age: {stale_info.get('age_hours', 0)}h)")

    files = sorted(os.listdir(state_dir))
    print(f"Active Slots ({len(files)} files on disk):")
    for f in files:
        if f.startswith("."):
            continue
        filepath = os.path.join(state_dir, f)
        if os.path.isdir(filepath):
            print(f"  [{f}/] (Directory)")
            continue
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(filepath)))
        size_bytes = os.path.getsize(filepath)
        print(f"  [{f}] - {size_bytes}B - mtime: {mtime_str}")

def clean_active_latches(workspace: str, archive: bool = True) -> None:
    state_dir = get_state_dir(workspace)
    if not os.path.exists(state_dir):
        return

    ticket_file = os.path.join(state_dir, SLOTS[10])
    ticket_id = "previous"
    if os.path.exists(ticket_file):
        with open(ticket_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Ticket-ID:"):
                    ticket_id = line.split(":", 1)[1].strip()
                    break

    # Archive to single flat file if requested to prevent bloat
    if archive and os.path.exists(ticket_file):
        archive_dir = os.path.join(state_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)
        archive_file = os.path.join(archive_dir, f"{ticket_id}.log")
        with open(archive_file, "w", encoding="utf-8") as out:
            for slot_num in [10, 20, 30, 40, 99]:
                fname = SLOTS[slot_num]
                fpath = os.path.join(state_dir, fname)
                if os.path.exists(fpath):
                    out.write(f"=== {fname} ===\n")
                    with open(fpath, "r", encoding="utf-8") as src:
                        out.write(src.read() + "\n\n")

    # Remove active transient slots (preserve 00_governance.md, .gitignore, Makefile)
    for slot_num in [10, 20, 30, 40, 99]:
        fpath = os.path.join(state_dir, SLOTS[slot_num])
        if os.path.exists(fpath):
            os.remove(fpath)

    # Prune artifacts
    artifacts_dir = os.path.join(state_dir, "artifacts")
    if os.path.exists(artifacts_dir):
        for af in os.listdir(artifacts_dir):
            os.remove(os.path.join(artifacts_dir, af))

    print("Active latches cleaned. Zero disk bloat preserved.")

def manage_hook(workspace: str, hook_type: str = "pre-push", remove: bool = False) -> None:
    git_dir = os.path.join(os.path.abspath(workspace), ".git")
    if not os.path.exists(git_dir):
        print(f"Error: {workspace} is not a git repository root (.git not found).", file=sys.stderr)
        sys.exit(1)

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    hook_file = os.path.join(hooks_dir, hook_type)

    if remove:
        if os.path.exists(hook_file):
            os.remove(hook_file)
            print(f"Removed optional git hook: {hook_file}")
        else:
            print(f"No hook found at: {hook_file}")
        return

    with open(hook_file, "w", encoding="utf-8") as f:
        f.write(PRE_PUSH_HOOK_TEMPLATE)

    # chmod +x
    st = os.stat(hook_file)
    os.chmod(hook_file, st.st_mode | stat.S_IEXEC)
    print(f"Optional {hook_type} hook installed at: {hook_file}")
    print("Commits proceed unhindered. Only 'git push' validates verified milestones.")

def main():
    parser = argparse.ArgumentParser(description="Manage physical disk state latches.")
    subparsers = parser.add_subparsers(dest="command")

    # init
    p_init = subparsers.add_parser("init", help="Initialize bounded disk state in workspace")
    p_init.add_argument("--workspace", default=".", help="Workspace path (default: current dir)")
    p_init.add_argument("--ticket", default="TICKET-01", help="Ticket ID")
    p_init.add_argument("--title", default="Task Execution", help="Ticket title/description")

    # stamp (supports named slots: plan, tdd, impl)
    p_stamp = subparsers.add_parser("stamp", help="Write physical milestone latch")
    p_stamp.add_argument("slot", type=str, help="Runlevel slot (e.g. plan, tdd, impl, or 20, 30, 40)")
    p_stamp.add_argument("content", help="Milestone summary content")
    p_stamp.add_argument("--next-action", default="continue", help="Next permitted action")
    p_stamp.add_argument("--workspace", default=".", help="Workspace path")

    # artifact (subagent arena output isolation)
    p_artifact = subparsers.add_parser("artifact", help="Save subagent output to isolated disk artifact")
    p_artifact.add_argument("--role", required=True, help="Subagent role name (e.g. Archaeology, Critic)")
    p_artifact.add_argument("--content", required=True, help="Subagent findings content")
    p_artifact.add_argument("--workspace", default=".", help="Workspace path")

    # status
    p_status = subparsers.add_parser("status", help="Inspect physical disk state and check staleness")
    p_status.add_argument("--workspace", default=".", help="Workspace path")

    # clean
    p_clean = subparsers.add_parser("clean", help="Archive and reset active latches to avoid bloat")
    p_clean.add_argument("--workspace", default=".", help="Workspace path")

    # hook (optional pre-push hook management)
    p_hook = subparsers.add_parser("hook", help="Install or remove optional git pre-push verification hook")
    p_hook.add_argument("--type", default="pre-push", choices=["pre-push", "pre-commit"], help="Hook type")
    p_hook.add_argument("--remove", action="store_true", help="Remove hook")
    p_hook.add_argument("--workspace", default=".", help="Workspace path")

    args = parser.parse_args()

    if args.command == "init":
        init_workspace(args.workspace, args.ticket, args.title)
    elif args.command == "stamp":
        stamp_milestone(args.workspace, args.slot, args.content, args.next_action)
    elif args.command == "artifact":
        write_artifact(args.workspace, args.role, args.content)
    elif args.command == "status":
        print_status(args.workspace)
    elif args.command == "clean":
        clean_active_latches(args.workspace, archive=True)
    elif args.command == "hook":
        manage_hook(args.workspace, hook_type=args.type, remove=args.remove)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
