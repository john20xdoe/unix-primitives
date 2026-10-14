# Dependency Graph Architecture
Build and execution lifecycles organize as a directed acyclic graph.
The build system coordinates targets using GNU Makefile conventions:
- Artifacts depend on explicit prerequisite files declaring build order.
- Target ci-gate specifies dependencies on test-green and lint-green.
- Phony targets declare non-file administrative actions explicitly.
- File modification timestamps drive automatic target invalidation.
Execution follows backward-chaining DAG resolution from terminal goals.
Cyclic transitions and manual procedural checklists are forbidden.
Targets build in topological sequence determined by prerequisite relationships.