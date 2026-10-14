#!/usr/bin/env python3
"""
state_manager.py - Physical disk state manager for prompt gravity.

Maintains bounded SysV runlevel disk latches (.state/00_... -> 99_...) in workspaces.
Supports named slots, pre-push hook management, and subagent artifact isolation.
"""

import sys
import os
import stat
import time
import argparse
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple

try:
    import fcntl
except ImportError:
    fcntl = None

ARCHIVE_KEEP = 20

def get_skills_source_dir() -> str:
    env_home = os.environ.get("UNIX_PRIMITIVES_HOME")
    if env_home:
        cand = os.path.abspath(os.path.expanduser(env_home))
        if os.path.isdir(os.path.join(cand, "skills")):
            return os.path.join(cand, "skills")
        return cand
    cand = Path(__file__).resolve().parent.parent.parent
    if cand.is_dir() and any(p.name.startswith("unix-") for p in cand.iterdir()):
        return str(cand)
    return os.path.expanduser("~/.gemini/config/skills")

SLOT_ALIASES = {
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
"""

MAKEFILE_TEMPLATE = """STATE_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
REPO_ROOT := $(patsubst %/,%,$(dir $(STATE_DIR)))

.PHONY: all status clean verify ci-gate

all: status

# Physical disk milestone targets
$(STATE_DIR)/20_plan.md: $(STATE_DIR)/10_ticket.md
	@echo "Awaiting plan creation and human signoff"

$(STATE_DIR)/30_tdd_red.md: $(STATE_DIR)/20_plan.md
	@echo "Awaiting TDD test creation"

$(STATE_DIR)/40_impl_green.md: $(STATE_DIR)/30_tdd_red.md
	@echo "Awaiting implementation verification"

ci-gate: $(STATE_DIR)/40_impl_green.md
	@python3 "{state_manager_path}" verify --workspace "$(REPO_ROOT)"

status:
	@python3 "{state_manager_path}" status --workspace "$(REPO_ROOT)"

clean:
	@python3 "{state_manager_path}" clean --workspace "$(REPO_ROOT)"
"""

HOOK_TEMPLATE = """#!/bin/sh
# unix-primitives-managed-hook
# Validates active ticket runlevel before allowing {hook_type}

# If a backup hook exists, replay stdin to both
if [ -x "$0.unix-primitives.bak" ]; then
    TMP_STDIN=$(mktemp)
    cat > "$TMP_STDIN"
    "$0.unix-primitives.bak" "$@" < "$TMP_STDIN"
    BAK_EXIT=$?
    if [ $BAK_EXIT -ne 0 ]; then
        rm -f "$TMP_STDIN"
        exit $BAK_EXIT
    fi
    rm -f "$TMP_STDIN"
fi

STATE_DIR="$(git rev-parse --show-toplevel 2>/dev/null)/.state"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

if [ -d "$STATE_DIR" ]; then
    echo "=== [unix-primitives] Validating {hook_type} runlevel ==="
    python3 "{state_manager_path}" verify --workspace "$REPO_ROOT"
    if [ $? -ne 0 ]; then
        echo "{hook_type} check failed: Active ticket in .state/ has unverified milestones."
        {failure_msg}
        exit 1
    fi
fi

exit 0
"""


def _locked_write(path: str, text: str, mode: str = "w", lock_path: Optional[str] = None) -> None:
    parent_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent_dir, exist_ok=True)
    if lock_path is None:
        abs_p = os.path.abspath(path)
        if "/.state" in abs_p:
            state_idx = abs_p.find("/.state")
            state_root = abs_p[:state_idx + len("/.state")]
            lock_path = os.path.join(state_root, ".lock")
        elif "/.git" in abs_p:
            git_idx = abs_p.find("/.git")
            git_root = abs_p[:git_idx + len("/.git")]
            lock_path = os.path.join(git_root, "unix-primitives.lock")
        else:
            lock_path = os.path.join(parent_dir, ".lock")

    lock_fd = None
    if fcntl is not None:
        try:
            lock_fd = open(lock_path, "w")
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        except Exception:
            lock_fd = None

    try:
        if "a" in mode:
            with open(path, "a", encoding="utf-8") as f:
                f.write(text)
        else:
            tmp_path = f"{path}.tmp.{os.getpid()}.{time.time_ns()}"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp_path, path)
    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
            except Exception:
                pass


def sanitize_id(s: str) -> str:
    """Sanitize identifier to keep only [A-Za-z0-9._-], mapping other chars to _, stripping leading dots."""
    if not s:
        return "UNKNOWN"
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", str(s))
    sanitized = sanitized.lstrip(".")
    if not sanitized:
        return "UNKNOWN"
    return sanitized


def get_state_dir(workspace: str) -> str:
    return os.path.join(os.path.abspath(workspace), ".state")


def resolve_slot(slot_identifier: str) -> int:
    key = str(slot_identifier).strip().lower()
    if key in SLOT_ALIASES:
        return SLOT_ALIASES[key]
    try:
        val = int(key)
        if val in (20, 30, 40):
            return val
    except ValueError:
        pass
    print(f"Error: '{slot_identifier}' is not a stampable milestone (plan|tdd|impl)", file=sys.stderr)
    sys.exit(1)


def read_headers(path: str) -> Tuple[Dict[str, str], str]:
    headers: Dict[str, str] = {}
    body_lines = []
    if not os.path.exists(path):
        return headers, ""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    in_headers = True
    for line in lines:
        if in_headers:
            if line.strip() == "":
                in_headers = False
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()
            else:
                in_headers = False
                body_lines.append(line)
        else:
            body_lines.append(line)
    return headers, "".join(body_lines)


def write_headers(path: str, headers: Dict[str, str], body: str = "") -> None:
    content = ""
    for k, v in headers.items():
        content += f"{k}: {v}\n"
    content += "\n"
    if body:
        content += body.lstrip("\n")
    _locked_write(path, content, mode="w")


def update_ticket(workspace: str, field: str, value: str) -> None:
    state_dir = get_state_dir(workspace)
    ticket_file = os.path.join(state_dir, SLOTS[10])
    if not os.path.exists(ticket_file):
        print(f"Error: {SLOTS[10]} not found in workspace", file=sys.stderr)
        sys.exit(1)

    normalized_field = field.strip()
    if normalized_field.lower() in ("ticket-id", "created"):
        print(f"Error: Field '{field}' cannot be updated", file=sys.stderr)
        sys.exit(1)

    headers, body = read_headers(ticket_file)
    headers[normalized_field] = value.strip()
    write_headers(ticket_file, headers, body)
    print(f"Updated ticket field '{normalized_field}' in {SLOTS[10]}")


def init_workspace(
    workspace: str,
    ticket_id: str,
    title: str,
    governance: Optional[str] = None,
    verify_cmd: str = "",
    track_governance: bool = False,
    force: bool = False
) -> None:
    state_dir = get_state_dir(workspace)
    os.makedirs(state_dir, exist_ok=True)

    ticket_path = os.path.join(state_dir, SLOTS[10])
    if os.path.exists(ticket_path) and not force:
        active_headers, _ = read_headers(ticket_path)
        active_id = active_headers.get("Ticket-ID", "UNKNOWN")
        print(f"Error: active ticket {active_id} exists; run 'clean' first or pass --force", file=sys.stderr)
        sys.exit(1)

    # 1. Write .gitignore
    gitignore_path = os.path.join(state_dir, ".gitignore")
    gi_content = GITIGNORE_CONTENT
    if track_governance:
        gi_content += "!00_governance.md\n"
    _locked_write(gitignore_path, gi_content, mode="w")

    # 2. Write 00_governance.md if not present
    gov_path = os.path.join(state_dir, SLOTS[0])
    if not os.path.exists(gov_path):
        default_gov = """# Root Governance & Invariants

- State Recovery: On session start or compaction, inspect .state/ and resume from highest runlevel.
- Invariant: Build and tests must pass at every milestone gate.
- Circuit Breaker: Trips at k=2 consecutive failures -> halt and escalate.
- Anti-Bloat: Active latches strictly bounded.
"""
        _locked_write(gov_path, governance or default_gov, mode="w")

    # 3. Clean active latches
    clean_active_latches(workspace, archive=True)

    # 4. Write 10_ticket.md
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ticket_headers = {
        "Ticket-ID": ticket_id,
        "Title": title,
        "Status": "IN_PROGRESS",
        "Created": now_iso,
        "Timestamp": now_iso,
    }
    ticket_body = f"## Requirements\n{title}\n"
    write_headers(ticket_path, ticket_headers, ticket_body)

    # 4b. Write tracked repo-level .unix-primitives if verify_cmd given
    if verify_cmd:
        repo_cfg = os.path.join(os.path.abspath(workspace), ".unix-primitives")
        cfg_headers, cfg_body = read_headers(repo_cfg)
        cfg_headers["Verify-Command"] = verify_cmd
        write_headers(repo_cfg, cfg_headers, cfg_body)
        print("Commit .unix-primitives to lock the gate.")

    # 5. Write volatile 99_next_action.md
    write_next_action(workspace, "plan", "10_ticket.md", "DRAFT_PLAN", ticket_id)

    # 6. Generate real Makefile for disk timestamp invalidation
    script_path = os.path.abspath(__file__)
    makefile_path = os.path.join(state_dir, "Makefile")
    _locked_write(makefile_path, MAKEFILE_TEMPLATE.format(state_manager_path=script_path), mode="w")

    print(f"Initialized physical disk state at: {state_dir}")
    print(f"Active ticket: [{ticket_id}] {title}")
    print("Disk slots strictly bounded.")


def link_project_agents(workspace: str) -> None:
    workspace_agents = os.path.join(os.path.abspath(workspace), ".agents", "skills")
    if not os.path.exists(workspace_agents):
        return

    global_skills_dir = get_skills_source_dir()
    if not os.path.exists(global_skills_dir):
        return

    unix_skills = [s for s in os.listdir(global_skills_dir) if s.startswith("unix-")]
    linked = []
    for s in unix_skills:
        src = os.path.join(global_skills_dir, s)
        dst = os.path.join(workspace_agents, s)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                os.symlink(src, dst)
                linked.append(s)
            except OSError:
                pass

    if linked:
        print(f"Auto-linked {len(linked)} unix primitives to workspace .agents/skills/: {', '.join(linked)}")
        print("Warning: symlinks in .agents/skills/ contain absolute paths to home directory; do not commit them to version control.")


def write_next_action(workspace: str, next_action: str, target_file: str, status: str, ticket_id: str) -> None:
    state_dir = get_state_dir(workspace)
    pointer_file = os.path.join(state_dir, SLOTS[99])
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    content = f"""Target: {target_file}
Status: {status}
Next-Action: {next_action}
Ticket-ID: {ticket_id}
Timestamp: {now_iso}
"""
    _locked_write(pointer_file, content, mode="w")


def stamp_milestone(workspace: str, slot_id: str, content: str, next_action: str, force: bool = False) -> None:
    slot_num = resolve_slot(slot_id)
    state_dir = get_state_dir(workspace)

    ticket_file = os.path.join(state_dir, SLOTS[10])
    if not os.path.exists(ticket_file) and not force:
        print(f"Error: prerequisite {SLOTS[10]} missing", file=sys.stderr)
        sys.exit(1)

    filename = SLOTS[slot_num]
    target_path = os.path.join(state_dir, filename)

    if not force:
        if slot_num == 20 and os.path.exists(target_path):
            print(f"Error: milestone {filename} is write-once; pass --force to overwrite", file=sys.stderr)
            sys.exit(1)
        elif slot_num == 30:
            plan_file = os.path.join(state_dir, SLOTS[20])
            if not os.path.exists(plan_file):
                print(f"Error: prerequisite {SLOTS[20]} missing", file=sys.stderr)
                sys.exit(1)
        elif slot_num == 40:
            tdd_file = os.path.join(state_dir, SLOTS[30])
            if not os.path.exists(tdd_file):
                print(f"Error: prerequisite {SLOTS[30]} missing", file=sys.stderr)
                sys.exit(1)

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _locked_write(target_path, f"Milestone: {filename}\nTimestamp: {now_iso}\n\n{content}\n", mode="w")

    # Read ticket ID if available
    ticket_id = "UNKNOWN"
    if os.path.exists(ticket_file):
        headers, _ = read_headers(ticket_file)
        ticket_id = headers.get("Ticket-ID", "UNKNOWN")

    # Invalidate higher milestone slots > slot_num
    invalidated = []
    for higher_slot in (20, 30, 40):
        if higher_slot > slot_num:
            higher_file = os.path.join(state_dir, SLOTS[higher_slot])
            if os.path.exists(higher_file):
                archive_dir = os.path.join(state_dir, "archive")
                os.makedirs(archive_dir, exist_ok=True)
                safe_ticket_id = sanitize_id(ticket_id)
                archive_file = os.path.join(archive_dir, f"{safe_ticket_id}.log")
                with open(higher_file, "r", encoding="utf-8") as hf:
                    hcontent = hf.read()
                arch_entry = f"=== INVALIDATED {SLOTS[higher_slot]} {now_iso} ===\n{hcontent}\n\n"
                _locked_write(archive_file, arch_entry, mode="a")
                try:
                    os.remove(higher_file)
                    invalidated.append(SLOTS[higher_slot])
                except OSError:
                    pass
    if invalidated:
        print(f"Invalidated: {', '.join(invalidated)}")

    write_next_action(workspace, next_action, filename, "PROGRESSING", ticket_id)
    print(f"Physical latch stamped: {filename} (Disk mtime updated)")


def verify_gate(workspace: str, allow_dirty_config: bool = False) -> bool:
    state_dir = get_state_dir(workspace)
    impl_file = os.path.join(state_dir, SLOTS[40])
    if not os.path.exists(impl_file):
        print(f"Error: Implementation milestone not verified ({SLOTS[40]} missing)", file=sys.stderr)
        sys.exit(1)

    # Check strict mtime order: mtime(10) <= mtime(20) <= mtime(30) <= mtime(40)
    for earlier_slot, later_slot in [(10, 20), (20, 30), (30, 40)]:
        p_earlier = os.path.join(state_dir, SLOTS[earlier_slot])
        p_later = os.path.join(state_dir, SLOTS[later_slot])
        if os.path.exists(p_earlier) and os.path.exists(p_later):
            if os.path.getmtime(p_later) < os.path.getmtime(p_earlier):
                print(f"Error: {SLOTS[later_slot]} older than {SLOTS[earlier_slot]}; re-stamp required", file=sys.stderr)
                sys.exit(1)

    # Check for deprecated ticket header
    ticket_file = os.path.join(state_dir, SLOTS[10])
    if os.path.exists(ticket_file):
        ticket_h, _ = read_headers(ticket_file)
        if "Verify-Command" in ticket_h:
            print("Warning: Verify-Command in 10_ticket.md is deprecated and ignored; use repo root .unix-primitives", file=sys.stderr)

    repo_cfg_path = os.path.join(os.path.abspath(workspace), ".unix-primitives")
    verify_cmd = ""
    if os.path.exists(repo_cfg_path):
        if not allow_dirty_config:
            try:
                res = subprocess.run(
                    ["git", "status", "--porcelain", ".unix-primitives"],
                    cwd=os.path.abspath(workspace),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                status_lines = res.stdout.splitlines()
                for s_line in status_lines:
                    if s_line.startswith((" M", "M ", "MM")):
                        print("Warning: verify command modified but uncommitted", file=sys.stderr)
                        sys.exit(1)
            except Exception:
                pass

        cfg_headers, _ = read_headers(repo_cfg_path)
        verify_cmd = cfg_headers.get("Verify-Command", "")

    if verify_cmd:
        print(f"Executing verify command from .unix-primitives: {verify_cmd}")
        res = subprocess.run(verify_cmd, shell=True, cwd=os.path.abspath(workspace))
        if res.returncode != 0:
            print(f"Error: Verify command failed with exit code {res.returncode}", file=sys.stderr)
            sys.exit(res.returncode)

    print("Verification gate passed.")
    return True


def write_artifact(workspace: str, role: str, content: str) -> None:
    state_dir = get_state_dir(workspace)
    artifacts_dir = os.path.join(state_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    sanitized_role = sanitize_id(role.lower())
    artifact_path = os.path.join(artifacts_dir, f"{sanitized_role}.md")
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    _locked_write(artifact_path, f"Role: {role}\nTimestamp: {now_iso}\n\n{content}\n", mode="w")

    print(f"Subagent artifact saved to disk: {artifact_path}")
    print("Orchestrator context preserved.")


def check_staleness(workspace: str) -> Dict[str, str]:
    state_dir = get_state_dir(workspace)
    if not os.path.exists(state_dir):
        return {"status": "UNINITIALIZED"}

    ticket_file = os.path.join(state_dir, SLOTS[10])
    if not os.path.exists(ticket_file):
        return {"status": "EMPTY"}

    mtimes = []
    for slot_num in [10, 20, 30, 40, 99]:
        p = os.path.join(state_dir, SLOTS[slot_num])
        if os.path.exists(p):
            mtimes.append(os.path.getmtime(p))

    latest_mtime = max(mtimes) if mtimes else os.path.getmtime(ticket_file)
    age_hours = (time.time() - latest_mtime) / 3600.0

    stale = age_hours > 72.0
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
        headers, _ = read_headers(ticket_file)
        ticket_id = headers.get("Ticket-ID", "previous")

    # Archive to single flat file if requested to prevent bloat
    if archive and os.path.exists(ticket_file):
        archive_dir = os.path.join(state_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)
        safe_ticket_id = sanitize_id(ticket_id)
        archive_file = os.path.join(archive_dir, f"{safe_ticket_id}.log")
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        arch_content = f"=== ARCHIVED {now_iso} ===\n"
        for slot_num in [10, 20, 30, 40, 99]:
            fname = SLOTS[slot_num]
            fpath = os.path.join(state_dir, fname)
            if os.path.exists(fpath):
                arch_content += f"=== {fname} ===\n"
                with open(fpath, "r", encoding="utf-8") as src:
                    arch_content += src.read() + "\n\n"
        _locked_write(archive_file, arch_content, mode="a")

        # Archive rotation cap: keep newest ARCHIVE_KEEP .log files
        log_files = [
            f for f in os.listdir(archive_dir)
            if f.endswith(".log") and not f.startswith("_")
        ]
        if len(log_files) > ARCHIVE_KEEP:
            log_files_sorted = sorted(
                log_files,
                key=lambda f: os.path.getmtime(os.path.join(archive_dir, f))
            )
            to_rotate = log_files_sorted[:-ARCHIVE_KEEP]
            rotated_log = os.path.join(archive_dir, "_rotated.log")
            rot_content = ""
            for rf in to_rotate:
                rf_path = os.path.join(archive_dir, rf)
                rot_content += f"=== ROTATED FROM {rf} ===\n"
                with open(rf_path, "r", encoding="utf-8") as src:
                    rot_content += src.read() + "\n\n"
                try:
                    os.remove(rf_path)
                except OSError:
                    pass
            _locked_write(rotated_log, rot_content, mode="a")

    # Remove active transient slots (preserve 00_governance.md, .gitignore, Makefile)
    for slot_num in [10, 20, 30, 40, 99]:
        fpath = os.path.join(state_dir, SLOTS[slot_num])
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except OSError:
                pass

    # Prune artifacts
    artifacts_dir = os.path.join(state_dir, "artifacts")
    if os.path.exists(artifacts_dir):
        for af in os.listdir(artifacts_dir):
            try:
                os.remove(os.path.join(artifacts_dir, af))
            except OSError:
                pass

    print("Active latches cleaned.")


def get_hooks_dir(workspace: str) -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"],
            cwd=os.path.abspath(workspace),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        hooks_rel = res.stdout.strip()
        if os.path.isabs(hooks_rel):
            return hooks_rel
        return os.path.normpath(os.path.join(os.path.abspath(workspace), hooks_rel))
    except Exception as e:
        print(f"Error: {workspace} is not a git repository root or git failed: {e}", file=sys.stderr)
        sys.exit(1)


def manage_hook(workspace: str, hook_type: str = "pre-push", remove: bool = False) -> None:
    hooks_dir = get_hooks_dir(workspace)
    os.makedirs(hooks_dir, exist_ok=True)
    hook_file = os.path.join(hooks_dir, hook_type)
    backup_file = f"{hook_file}.unix-primitives.bak"

    if remove:
        if os.path.exists(hook_file):
            with open(hook_file, "r", encoding="utf-8") as f:
                content = f.read()
            if "# unix-primitives-managed-hook" not in content:
                print(f"Error: Hook at {hook_file} was not installed by unix-primitives.", file=sys.stderr)
                sys.exit(1)
            os.remove(hook_file)
            print(f"Removed optional git hook: {hook_file}")
            if os.path.exists(backup_file):
                os.rename(backup_file, hook_file)
                print(f"Restored original hook from: {backup_file}")
        else:
            print(f"No hook found at: {hook_file}")
        return

    # Install
    if os.path.exists(hook_file):
        with open(hook_file, "r", encoding="utf-8") as f:
            content = f.read()
        if "# unix-primitives-managed-hook" not in content:
            if os.path.exists(backup_file):
                epoch = int(time.time())
                os.rename(backup_file, f"{backup_file}.{epoch}")
            os.rename(hook_file, backup_file)
            print(f"Existing {hook_type} hook preserved as: {backup_file}")

    if hook_type == "pre-commit":
        failure_msg = 'echo "Fix milestone or run /unix-clean before committing."'
    else:
        failure_msg = 'echo "Local commits remain safe. Fix milestone or run /unix-clean before proceeding."'

    script_path = os.path.abspath(__file__)
    hook_body = HOOK_TEMPLATE.format(
        hook_type=hook_type,
        failure_msg=failure_msg,
        state_manager_path=script_path
    )
    _locked_write(hook_file, hook_body, mode="w")

    st = os.stat(hook_file)
    os.chmod(hook_file, st.st_mode | stat.S_IEXEC)
    print(f"Optional {hook_type} hook installed at: {hook_file}")
    if hook_type == "pre-push":
        print("Commits proceed unhindered. Only 'git push' validates verified milestones.")
    else:
        print("Validates verified milestones before commit.")


def main():
    parser = argparse.ArgumentParser(description="Manage physical disk state latches.")
    subparsers = parser.add_subparsers(dest="command")

    # init
    p_init = subparsers.add_parser("init", help="Initialize bounded disk state in workspace")
    p_init.add_argument("--workspace", default=".", help="Workspace path (default: current dir)")
    p_init.add_argument("--ticket", default="TICKET-01", help="Ticket ID")
    p_init.add_argument("--title", default="Task Execution", help="Ticket title/description")
    p_init.add_argument("--verify", dest="verify_cmd", default="", help="Verification command executed at ci-gate")
    p_init.add_argument("--track-governance", action="store_true", help="Allow git tracking of 00_governance.md")
    p_init.add_argument("--force", action="store_true", help="Force initialization even if active ticket exists")

    # update-ticket
    p_update = subparsers.add_parser("update-ticket", help="Update single RFC 822 header in 10_ticket.md")
    p_update.add_argument("--field", required=True, help="Header field to update")
    p_update.add_argument("--value", required=True, help="New header value")
    p_update.add_argument("--workspace", default=".", help="Workspace path")

    # stamp (supports named slots: plan, tdd, impl)
    p_stamp = subparsers.add_parser("stamp", help="Write physical milestone latch")
    p_stamp.add_argument("slot", type=str, help="Runlevel slot (e.g. plan, tdd, impl, or 20, 30, 40)")
    p_stamp.add_argument("content", help="Milestone summary content")
    p_stamp.add_argument("--next-action", default="continue", help="Next permitted action")
    p_stamp.add_argument("--force", action="store_true", help="Force milestone stamp overriding prerequisites")
    p_stamp.add_argument("--workspace", default=".", help="Workspace path")

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify milestone gates and run verification command")
    p_verify.add_argument("--allow-dirty-config", action="store_true", help="Allow uncommitted changes to .unix-primitives")
    p_verify.add_argument("--workspace", default=".", help="Workspace path")

    # artifact (subagent arena output isolation)
    p_artifact = subparsers.add_parser("artifact", help="Save subagent output to isolated disk artifact")
    p_artifact.add_argument("--role", required=True, help="Subagent role name (e.g. Archaeology, Critic)")
    p_artifact.add_argument("--content", default=None, help="Subagent findings content (or '-' / omit to read stdin)")
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

    # link-agents (link global skills into local .agents/skills/)
    p_link = subparsers.add_parser("link-agents", help="Symlink global unix skills into local .agents/skills/")
    p_link.add_argument("--workspace", default=".", help="Workspace path")

    args = parser.parse_args()

    if args.command == "init":
        init_workspace(
            args.workspace,
            args.ticket,
            args.title,
            verify_cmd=args.verify_cmd,
            track_governance=args.track_governance,
            force=args.force
        )
    elif args.command == "update-ticket":
        update_ticket(args.workspace, args.field, args.value)
    elif args.command == "link-agents":
        link_project_agents(args.workspace)
    elif args.command == "stamp":
        stamp_milestone(args.workspace, args.slot, args.content, args.next_action, force=args.force)
    elif args.command == "verify":
        verify_gate(args.workspace, allow_dirty_config=args.allow_dirty_config)
    elif args.command == "artifact":
        content = args.content
        if content is None or content == "-":
            content = sys.stdin.read()
        write_artifact(args.workspace, args.role, content)
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
