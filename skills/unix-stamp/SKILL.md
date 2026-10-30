---
name: unix-stamp
description: >
  Write physical milestone latch to disk with named aliases (plan, tdd, impl).
  Usage: /unix-stamp <plan|tdd|impl> "<summary>" [--next-action "<action>"] [--force]
---

# Unix State Stamp

## Direct Execution Protocol
Execute milestone stamping directly using native workspace file tools (`write_to_file`, `view_file`).
Do NOT invoke shell commands (`run_command`) or python scripts—native tool execution avoids repeated IDE permission prompts on variable milestone summaries.

### Named Runlevel Slots:
* `plan` -> `.state/20_plan.md` (Architecture & plan signoff latch; write-once unless `--force`)
* `tdd`  -> `.state/30_tdd_red.md` (Failing test verification latch; requires plan)
* `impl` -> `.state/40_impl_green.md` (Passing implementation latch; requires tdd)

---

## Step-by-Step Procedure

### 1. Prerequisite Check
* Read `Ticket-ID` from `.state/10_ticket.md`. If missing and not `--force`:
  Fail: `Error: prerequisite 10_ticket.md missing`
* If stamping `plan`:
  If `.state/20_plan.md` already exists and `--force` is **not** set:
  Fail: `Error: milestone 20_plan.md is write-once; pass --force to overwrite`
* If stamping `tdd`:
  If `.state/20_plan.md` does not exist and `--force` is **not** set:
  Fail: `Error: prerequisite 20_plan.md missing`
* If stamping `impl`:
  If `.state/30_tdd_red.md` does not exist and `--force` is **not** set:
  Fail: `Error: prerequisite 30_tdd_red.md missing`

### 2. Write Milestone Latch
Write target milestone file (`.state/20_plan.md`, `30_tdd_red.md`, or `40_impl_green.md`):
```markdown
Milestone: <slot_filename>
Timestamp: <ISO-timestamp>

<summary>
```

### 3. Invalidate Higher Slots
If stamping a lower slot than existing higher latches (e.g. re-stamping `plan` while `30_tdd_red.md` exists):
* For each higher slot file present:
  Append its contents to `.state/archive/<ticket-id>.log`:
  ```
  === INVALIDATED <slot_filename> <ISO-timestamp> ===
  <content>
  ```
  Delete the higher slot file from disk.

### 4. Update Volatile Pointer (`99_next_action.md`)
Write `.state/99_next_action.md`:
```markdown
Target: <slot_filename>
Status: PROGRESSING
Next-Action: <action (default: continue)>
Ticket-ID: <ticket-id>
Timestamp: <ISO-timestamp>
```

### 5. Confirmation Output
Confirm latch to user:
```
Physical latch stamped: <slot_filename> (Disk mtime updated)
```

---

## CLI Fallback
If invoked outside agent environment or in shell scripts:
```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py stamp <plan|tdd|impl> "<summary>" [--next-action "<action>"] [--force]
```
