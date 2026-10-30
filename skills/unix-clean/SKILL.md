---
name: unix-clean
description: >
  Archive completed ticket latches and reset .state/ directory to clean slate (bounded active slots, archive rotated at 20 logs).
  Usage: /unix-clean
---

# Unix State Clean

## Direct Execution Protocol
Execute latch cleanup directly using native workspace file tools (`write_to_file`, `view_file`, `list_dir`).
Do NOT invoke shell commands (`run_command`) or python scripts—native tool execution avoids IDE execution permission prompts.

---

## Step-by-Step Procedure

### 1. Read Active Ticket
Check `.state/10_ticket.md`:
* If present, read `Ticket-ID` from header (fallback: `previous`).
* If not present, skip archiving step.

### 2. Archive Active Latches
If `.state/10_ticket.md` exists:
* Read contents of each active latch on disk (`10_ticket.md`, `20_plan.md`, `30_tdd_red.md`, `40_impl_green.md`, `99_next_action.md`).
* Append to `.state/archive/<ticket-id>.log`:
  ```
  === ARCHIVED <ISO-timestamp> ===
  === <filename> ===
  <content>
  ```
* Enforce rotation cap: if `.state/archive/` contains > 20 `.log` files (excluding `_rotated.log`), append oldest beyond 20 to `_rotated.log` and delete them.

### 3. Clear Transient Slots
* Delete existing transient files:
  - `.state/10_ticket.md`
  - `.state/20_plan.md`
  - `.state/30_tdd_red.md`
  - `.state/40_impl_green.md`
  - `.state/99_next_action.md`
* Delete any files inside `.state/artifacts/`.
* **Preserve** immutable files: `.state/00_governance.md`, `.state/.gitignore`, `.state/Makefile`.

### 4. Confirmation Output
Confirm cleanup:
```
Active latches cleaned.
```

---

## CLI Fallback
If invoked outside agent environment or in shell scripts:
```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py clean
```
