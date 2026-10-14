# Commit Topology Protocol
Change series follow Linux Kernel Mailing List PATCH series conventions.
Proposed modifications organize into discrete topological commits:
- Patch zero provides the architectural summary and dependency ordering.
- Early patches introduce domain abstractions, data models, and interfaces.
- Intermediate patches implement feature behaviors across subsystem boundaries.
- Final patches connect integration entry points and end-to-end tests.
The invariant requires git rebase with exec flag running verification.
Every intermediate commit hash in the history independently builds and passes.
Commit messages state motivation, design tradeoffs, and technical consequences.