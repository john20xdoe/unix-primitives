---
name: unix-init
description: >
  Initialize bounded physical disk state (.state/) in current workspace with real Makefile and SysV runlevel latches.
  Usage: /unix-init [--force] [--verify-cmd "<cmd>"] [--track-governance] [<ticket-id>] [<title>]
---

# Unix State Init

## Action
When `/unix-init` is invoked, execute the physical workspace state bootstrapper:

```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py init --workspace . --ticket "<ticket-id>" --title "<title>" [--verify-cmd "<command>"] [--track-governance] [--force]
```

* `--force`: Archive active ticket and reset state if ticket already exists.
* `--verify-cmd "<cmd>"`: Set custom automated test/verification command in ticket header.
* `--track-governance`: Do not gitignore `00_governance.md` so governance rules can be committed.

Output status and confirm disk state is initialized with strict bounded slots.
