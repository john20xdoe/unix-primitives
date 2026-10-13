---
name: unix-clean
description: >
  Archive completed ticket latches and reset .state/ directory to clean slate (zero bloat).
  Usage: /unix-clean
---

# Unix State Clean

## Action
When `/unix-clean` is invoked, purge active transient slots and archive previous ticket to flat log:

```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py clean
```

Report confirmation that active slots were cleared and zero-bloat invariant preserved.
