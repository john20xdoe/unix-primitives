---
name: unix-init
description: >
  Initialize bounded physical disk state (.state/) in current workspace with real Makefile and SysV runlevel latches.
  Usage: /unix-init [ticket-id] [title]
---

# Unix State Init

## Action
When `/unix-init` is invoked, execute the physical workspace state bootstrapper:

```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py init --workspace . --ticket "${1:-TASK-01}" --title "${2:-Active Task}"
```

Output status and confirm disk state is initialized with strict $O(1)$ bounded slots.
