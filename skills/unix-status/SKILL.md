---
name: unix-status
description: >
  Inspect physical disk state runlevels, mtime timestamps, and staleness health in current workspace.
  Usage: /unix-status
---

# Unix State Status

## Action
When `/unix-status` is invoked, inspect the current physical disk state:

```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py status
```

Report active slots, disk timestamps, and whether state is ACTIVE or STALE.
