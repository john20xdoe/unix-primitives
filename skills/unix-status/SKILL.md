---
name: unix-status
description: >
  Inspect physical disk state runlevels, mtime timestamps, and staleness health in current workspace.
  Usage: /unix-status
---

# Unix State Status

## Direct Execution Protocol
Inspect state directly using native workspace tools (`list_dir`, `view_file`).
Do NOT invoke shell commands (`run_command`) or python scripts—native inspection avoids IDE execution permission prompts.

---

## Step-by-Step Procedure

### 1. Directory Check
Check if `.state/` directory exists:
* If not present, report:
  `Status: .state/ directory not initialized.`

### 2. State & Staleness Health
* Check if `.state/10_ticket.md` exists:
  - If missing: State is `EMPTY`.
  - If present: Inspect file modification timestamps (`mtime`) of all present transient slot files (`10_ticket.md`, `20_plan.md`, `30_tdd_red.md`, `40_impl_green.md`, `99_next_action.md`).
  - Calculate staleness: if age since newest active latch > 72 hours, state is `STALE`; otherwise `ACTIVE`.

### 3. Report Active Slots
Report formatted status:
```
=== Physical Disk State Status ===
Location: <workspace>/.state
State Health: <ACTIVE|STALE|EMPTY> (Age: <age>h)
Active Slots (<N> files on disk):
  [<filename>] - <size>B - mtime: <timestamp>
```

---

## CLI Fallback
If invoked outside agent environment or in shell scripts:
```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py status
```
