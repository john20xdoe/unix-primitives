---
name: unix-stamp
description: >
  Write physical milestone latch to disk with named aliases (plan, tdd, impl).
  Usage: /unix-stamp <plan|tdd|impl> "<summary>" [--next-action "<action>"] [--force]
---

# Unix State Stamp

## Action
When `/unix-stamp` is invoked, stamp the named milestone into `.state/`:

```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py stamp <plan|tdd|impl> "<summary>" [--next-action "<action>"] [--force]
```

### Named Runlevel Slots:
* `plan` -> `.state/20_plan.md` (Architecture & plan signoff latch; write-once unless `--force`)
* `tdd`  -> `.state/30_tdd_red.md` (Failing test verification latch; requires plan)
* `impl` -> `.state/40_impl_green.md` (Passing implementation latch; requires tdd)

* `--next-action "<action>"`: Record next permitted action in volatile pointer `99_next_action.md`.
* `--force`: Override prerequisite latches or allow re-stamping `plan`.

Advances disk mtime, updates volatile pointer `99_next_action.md`, and confirms runlevel advance.
