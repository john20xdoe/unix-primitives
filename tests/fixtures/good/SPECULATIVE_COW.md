# Ephemeral Worktree Isolation
Exploratory code modifications isolate within copy-on-write git worktrees.
Experimental mutation workflows follow transactional isolation patterns:
- A scratch worktree is created pointing to a detached ephemeral branch.
- Automated test suites evaluate candidate changes inside the isolated tree.
- Successful verification triggers a fast-forward merge into the primary branch.
- Unsuccessful verification triggers immediate worktree removal and branch deletion.
The primary repository working directory remains completely untouched during tests.
Transactional branch disposal guarantees zero leftover files after failures.
Working trees operate in parallel without conflicting lock contentions.