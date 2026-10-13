---
name: unix-hook
description: >
  Manage optional git pre-push verification hook (allows commits unhindered, checks milestones on push).
  Usage: /unix-hook [install|remove] [--type pre-push|pre-commit]
---

# Unix Git Hook Manager

## Action
When `/unix-hook` is invoked, manage git verification hook in current repository:

### Install Optional Pre-Push Hook (Default)
```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py hook --type "${2:-pre-push}"
```
* **Safe Invariant**: User commits proceed without blockage. Commits are never rejected during work.
* Only `git push` runs `.state/Makefile` validation (`ci-gate`), preventing broken milestones from reaching upstream while preserving local commits.

### Remove Hook
```bash
python3 ~/.gemini/config/skills/unix-primitives/scripts/state_manager.py hook --remove --type "${2:-pre-push}"
```
