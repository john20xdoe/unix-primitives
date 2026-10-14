# Atomic Multi-Package Coordination
Cross-package mutations execute under a Two-Phase Commit protocol.
Transactional updates coordinate through write-ahead logging mechanisms:
- Phase 1 (Prepare): each participant package builds and tests in scratch worktrees.
- Participants vote PREPARED only upon clean test compilation and verification.
- Phase 2 (Decide): the coordinator issues COMMIT if and only if all vote PREPARED.
- If any single participant votes ABORT, the coordinator issues full ROLLBACK.
Write-ahead logs record transaction states to disk before executing mutations.
Intermediate failures trigger automated rollback cleaning all modified worktrees.
The repository transitions atomically between globally verified consistent states.
Partial or broken multi-package states are mathematically eliminated.