---
name: unix-init
description: >
  Initialize bounded physical disk state (.state/) in current workspace with real Makefile and SysV runlevel latches.
  Usage: /unix-init [--force] [--verify-cmd "<cmd>"] [--track-governance] [<ticket-id>] [<title>]
---

# Unix State Init

## Direct Execution Protocol
Execute initialization directly using native workspace file tools (`write_to_file`, `view_file`, `list_dir`).
Do NOT invoke shell commands (`run_command`) or python scripts—native tool execution avoids repeated IDE permission prompts on variable ticket arguments.

### Arguments
* `<ticket-id>`: Unique ticket identifier (default: `TICKET-01`).
* `<title>`: Ticket summary or title (default: `Task Execution`).
* `--force`: Archive active ticket and overwrite existing state.
* `--verify-cmd "<cmd>"`: Set repo verification command in `.unix-primitives`.
* `--track-governance`: Exclude `00_governance.md` from `.state/.gitignore`.

---

## Step-by-Step Procedure

### 1. Active State Check
Check if `.state/10_ticket.md` exists:
* If exists and `--force` is **not** set:
  Fail immediately:
  `Error: active ticket <TICKET-ID> exists; run /unix-clean first or pass --force`
* If exists and `--force` **is** set:
  Read `Ticket-ID` from `10_ticket.md` (fallback: `previous`).
  Read contents of all existing transient latches (`10_ticket.md`, `20_plan.md`, `30_tdd_red.md`, `40_impl_green.md`, `99_next_action.md`).
  Append to `.state/archive/<ticket-id>.log` under header `=== ARCHIVED <ISO-timestamp> ===\n`.
  Delete previous transient latch files and any files under `.state/artifacts/`.

### 2. Write `.state/.gitignore`
Write `.state/.gitignore`:
```
# Prevent agent transient latches from polluting repository history
*
!.gitignore
```
If `--track-governance` is specified, append:
```
!00_governance.md
```

### 3. Write `.state/00_governance.md`
If `.state/00_governance.md` does not already exist, write:
```markdown
# Root Governance & Invariants

- State Recovery: On session start or compaction, inspect .state/ and resume from highest runlevel.
- Invariant: Build and tests must pass at every milestone gate.
- Circuit Breaker: Trips at k=2 consecutive failures -> halt and escalate.
- Anti-Bloat: Active latches strictly bounded.
```

### 4. Write `.state/10_ticket.md`
Write RFC 822 formatted header:
```markdown
Ticket-ID: <ticket-id>
Title: <title>
Status: IN_PROGRESS
Created: <ISO-timestamp>
Timestamp: <ISO-timestamp>

## Requirements
<title>
```

### 5. Write `.state/99_next_action.md`
Write volatile progress pointer:
```markdown
Target: 10_ticket.md
Status: DRAFT_PLAN
Next-Action: plan
Ticket-ID: <ticket-id>
Timestamp: <ISO-timestamp>
```

### 6. Write `.state/Makefile`
Write deterministic build and milestone DAG:
```makefile
STATE_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
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
	@python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py verify --workspace "$(REPO_ROOT)"

status:
	@python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py status --workspace "$(REPO_ROOT)"

clean:
	@python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py clean --workspace "$(REPO_ROOT)"
```

### 7. Repo Verification Config (Optional)
If `--verify-cmd "<command>"` is provided:
Write or update `.unix-primitives` at repository root:
```
Verify-Command: <command>
```

### 8. Confirmation Output
Confirm state initialization to user:
```
Initialized physical disk state at: .state/
Active ticket: [<ticket-id>] <title>
Disk slots strictly bounded.
```

---

## CLI Fallback
If invoked outside agent environment or in shell scripts:
```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py init --workspace . --ticket "<ticket-id>" --title "<title>" [--verify-cmd "<command>"] [--track-governance] [--force]
```
