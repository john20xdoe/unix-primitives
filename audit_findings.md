**What this repo does:** `unix-primitives` is a Python CLI and agent-skill suite that scans LLM prompt files for fragile prose anti-patterns, manages disk-backed task milestones in `.state/`, and benchmarks prompt variants (`prose`, `bespoke`, `canonical`, `host`) through an evaluation harness.
**Assumed load:** Single developer or coding agent running CLI commands locally, with occasional concurrent subagents sharing one workspace `.state/` directory and sequential multi-trial benchmark runs (`eval/run_ab.py`).

### Must fix

1. **`AGENT_CMD.format()` crashes on shell or JSON braces** ([eval/run_ab.py](file:///Volumes/Dev/lab/unix-primitives/eval/run_ab.py#L302-L308))
   - **What this is:** Benchmark runner substitutes `{model}`, `{prompt_file}`, `{task_dir}`, `{task_name}`, and `{variant}` into `AGENT_CMD` before launching each trial.
   - **Problem:** Python `str.format()` parses every `{...}` in `AGENT_CMD` as format field, so shell variables (`${1}`), `awk '{print $1}'`, or JSON flags (`'{"model": "{model}"}'`) crash immediately with `KeyError` or `ValueError`.
   - **Fix:** Replace `agent_cmd.format(...)` with literal `.replace(f"{{{k}}}", shlex.quote(str(v)))` over the 5 template keys.
   - **If we skip it:** Any `AGENT_CMD` containing shell braces or JSON arguments crashes on iteration 1.

2. **Concurrent `clean` or `init --force` races with `stamp` and corrupts archive** ([state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L277-L333), [state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L582-L654))
   - **What this is:** `init_workspace` and `clean_active_latches` check active ticket state, archive `.state/` files, rotate `.log` files past 20, and delete slots `10`..`99`.
   - **Problem:** Unlike `stamp_milestone` and `update_ticket`, neither function holds `state_lock` (`flock`, OS file lock) across its check-archive-delete sequence. Concurrent subagents can both pass `if os.path.exists(ticket_path) and not force`, archive same ticket twice, crash with `FileNotFoundError` at `open(rf_path)` when rotating a log just removed by another process, or delete a milestone latch just written by concurrent `stamp`.
   - **Fix:** Wrap bodies of `init_workspace` and `clean_active_latches` in `with state_lock(os.path.join(state_dir, ".lock")):` (lock is already thread-reentrant via `_lock_tls`).
   - **If we skip it:** Concurrent subagents crash during archive rotation or silently delete newly stamped milestones.

3. **Substring lock-path lookup creates stray directories outside workspace and litters custom hooks dir** ([state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L129-L141))
   - **What this is:** `_locked_write` infers lockfile path by searching target path string for `"/.state"` or `"/.git"`.
   - **Problem:** `abs_p.find("/.state")` and `abs_p.find("/.git")` match prefix substrings anywhere in parent path: workspace under `/Users/dev/.github/repo` matches `"/.git"` at `/.github` and writes `/Users/dev/.git/unix-primitives.lock`, while custom `core.hooksPath` (`custom-hooks/`) lacks `"/.git"` and leaves `custom-hooks/.lock` inside tracked hooks directory. `core.hooksPath=.githooks` avoids litter only by luck (`/.githooks` substring-matches `"/.git"`); existing `test_no_lock_litter_in_hooks_dir` checks `.git/hooks` only.
   - **Fix:** Match exact path components (`Path(abs_p).parts`) for `.state` or `.git`, and pass explicit `lock_path` from `manage_hook`.
   - **If we skip it:** Workspaces under `.github`, `.gitconfig`, or `.state*` parent folders create stray lock directories outside repo or fail with `PermissionError`, and custom hook directories get `.lock` litter.

4. **`.state/Makefile` lists `verify` in `.PHONY` with no rule, and missing-milestone recipes exit 0** ([state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L65-L90), [skills/unix-init/SKILL.md](file:///Volumes/Dev/lab/unix-primitives/skills/unix-init/SKILL.md#L85-L111))
   - **What this is:** Generated `.state/Makefile` defines build dependency graph (`20_plan.md` -> `30_tdd_red.md` -> `40_impl_green.md` -> `ci-gate`).
   - **Problem:** `.PHONY` declares `verify`, but no `verify:` rule exists (`make -f .state/Makefile verify` fails with `make: *** No rule to make target 'verify'.  Stop.`). Also, milestone recipes only run `@echo "Awaiting ..."` (exit 0), so `make -f .state/Makefile .state/20_plan.md` exits 0 even when `20_plan.md` is missing.
   - **Fix:** Add `verify: ci-gate` rule to `MAKEFILE_TEMPLATE` and `skills/unix-init/SKILL.md`.
   - **If we skip it:** Running `make -f .state/Makefile verify` fails with missing target error.

5. **Pre-registration gate fails on custom `--prompts-dir` and prints outdated `mtime` error** ([eval/run_ab.py](file:///Volumes/Dev/lab/unix-primitives/eval/run_ab.py#L71-L94), [eval/run_ab.py](file:///Volumes/Dev/lab/unix-primitives/eval/run_ab.py#L176-L192))
   - **What this is:** `check_preregistration_gate` verifies `PREREGISTRATION.md` was committed at or after last prompt edit before benchmark runs.
   - **Problem:** `prereg_file` is hardcoded to `Path(__file__).parent / "PREREGISTRATION.md"` while `git` runs in `prompts_dir`, breaking `--prompts-dir` when pointed outside `eval/`. Worse, error message still tells user `PREREGISTRATION.md` must `"have mtime >= all prompt files"`, whereas gate checks `git status --porcelain` cleanliness and commit timestamps (`%ct`) — so running `touch eval/PREREGISTRATION.md` dirties working tree and causes gate to fail.
   - **Fix:** Resolve `prereg_file` as `prompts_dir.parent / "PREREGISTRATION.md"` and update error message to state that `PREREGISTRATION.md` and `prompts/` must be clean in git with `PREREGISTRATION.md` committed at or after `prompts/`.
   - **If we skip it:** Users following error message (`touch PREREGISTRATION.md`) dirty repo and lock themselves out of running `run_ab.py`.

6. **Colon in `--field` or newline in `--role` corrupts RFC 822 headers** ([state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L233-L261), [state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L516-L526))
   - **What this is:** `write_headers` writes `k: v` lines for `update-ticket`, and `write_artifact` writes `Role: {role}` header in `.state/artifacts/<role>.md`.
   - **Problem:** `write_headers` rejects newlines in keys and values (fixed F3 below), but allows `:` or empty string in key `k` (`--field "A:B" --value "c"` writes `A:B: c`, which `read_headers` parses back as key `"A"` and value `"B: c"`). Meanwhile, `write_artifact` does not call `reject_newlines(role)` before writing `Role: {role}\n`.
   - **Fix:** In `write_headers`, reject empty keys or keys containing `:`, and call `reject_newlines(role)` in `write_artifact`.
   - **If we skip it:** `update-ticket --field "A:B"` silently corrupts header key on next read, and newline in `--role` injects forged headers into artifact files.

### Should fix

7. **`scan_directory` picks alphabetical first file instead of highest friction and emits broken relative path on `.`** ([unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L588), [unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L653-L658), [unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L728))
   - **What this is:** `scan_directory` and `generate_subagent_prompt` compute relative paths and recommend `/unix-primitives convert <file>` for top high-friction file.
   - **Problem:** `os.path.relpath(fpath, os.path.dirname(dir_path))` computes path relative to parent of `dir_path`, so scanning `.` prefixes every path with repo directory name (`unix-primitives/README.md`), which fails with `Target path not found` when passed to `convert`. Also, `top_target = high_friction[0]` selects from alphabetically sorted `file_results`, picking `a.md` (score `0/100` with keyword hit) over `z.md` (score `100/100`).
   - **Fix:** Use `os.path.relpath(fpath)` relative to current working directory, and pick `max(high_friction, key=lambda r: (r["score"], len(r["findings"])))`.
   - **If we skip it:** Directory scan recommends wrong file to refactor and outputs broken paths when scanning `.`.

8. **`strip_code` closes 4-backtick fences at first inner 3-backtick fence** ([unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L289-L301))
   - **What this is:** `strip_code` removes fenced code blocks before regex scanning so code examples do not trigger false positives.
   - **Problem:** Regex ``r"```+([^\n]*)\n([\s\S]*?)```+"`` does not backreference opening backtick count. When a markdown file uses 4-backtick fences (```` ```` ````) wrapping examples with inner ```` ``` ```` blocks, `strip_code` stops at first inner ```` ``` ```` and scans remaining code as prose.
   - **Fix:** Backreference opening fence length: ``r"(`{3,})([^\n]*)\n([\s\S]*?)\1"``.
   - **If we skip it:** Skill and documentation files with nested code fences produce false-positive hits inside code blocks.

9. **`scan_text` matches anti-patterns that start in prose and end inside short inline code spans** ([unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L307-L320))
   - **What this is:** `scan_text` ignores inline backtick code spans shorter than 38 characters (`short_backtick_spans`).
   - **Problem:** Line 318 only checks whether match start `m.start()` falls inside backtick span (`s_start <= start < s_end`). Multi-word regexes with `[\s\S]{1,60}` (like `CIRCUIT_BREAKER`) start in prose (`On failure, run`) and match keyword inside inline code (`` `tool --retry` ``).
   - **Fix:** Replace `< 38`-char inline backtick spans in `body` with spaces (`re.sub(r"`[^`\n]{1,35}`", " ", body)`) before pattern loop, and delete `short_backtick_spans` (-8 lines).
   - **If we skip it:** Prose followed by short CLI flags in backticks triggers false-positive friction findings.

10. **`verify_gate` silently passes if `git status` errors while `.unix-primitives` is missing** ([state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L472-L496))
    - **What this is:** `verify_gate` checks git status to block uncommitted edits or deletion of `.unix-primitives` before running `Verify-Command`.
    - **Problem:** Line 481 checks `if res.returncode == 0 and res.stdout.strip():` and line 495 swallows all exceptions (`except Exception: pass`). If `git status` exits non-zero (e.g., exit 128 from bad global `.gitconfig` or `safe.directory`) and `.unix-primitives` was deleted from working tree, `verify_gate` skips both checks and passes without running `Verify-Command`.
    - **Fix:** Fail closed (`sys.exit(1)`) when `res.returncode != 0` unless `allow_dirty_config=True`.
    - **If we skip it:** Any git error during `verify` silently bypasses `.unix-primitives` tamper check.

11. **Four `SKILL.md` files duplicate `state_manager.py` in prose and bypass `flock` locking** ([skills/unix-init/SKILL.md](file:///Volumes/Dev/lab/unix-primitives/skills/unix-init/SKILL.md#L10-L127), [skills/unix-stamp/SKILL.md](file:///Volumes/Dev/lab/unix-primitives/skills/unix-stamp/SKILL.md#L10-L71), [skills/unix-status/SKILL.md](file:///Volumes/Dev/lab/unix-primitives/skills/unix-status/SKILL.md#L10-L38), [skills/unix-clean/SKILL.md](file:///Volumes/Dev/lab/unix-primitives/skills/unix-clean/SKILL.md#L10-L50))
    - **What this is:** `unix-init`, `unix-stamp`, `unix-status`, and `unix-clean` instruct agent to manually read/write `.state/` files with LLM file tools instead of running `state_manager.py`.
    - **Problem:** Re-implementing `state_manager.py` in English prose bypasses `flock` file locking and atomic temp-file writes, burns multiple LLM tool turns per command, and has already drifted (`unix-init/SKILL.md` lines 30-35 omits the 20-log archive rotation enforced by `state_manager.py` and `unix-clean/SKILL.md`).
    - **Fix:** Instruct agent to run `state_manager.py` directly in all 4 `SKILL.md` files and delete duplicated prose state-machine steps (-230 lines).
    - **If we skip it:** Slash commands bypass host-level `flock` locking and prose instructions keep drifting from `state_manager.py`.

12. **`_rotated.log` and repeated-ticket `.log` files grow without bound** ([state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L610-L633))
    - **What this is:** `clean_active_latches` rotates `.state/archive/*.log` files past `ARCHIVE_KEEP = 20` into `_rotated.log`.
    - **Problem:** Write order fixed (F5 below), size still unbounded. Evicted logs are appended (`mode="a"`) to `_rotated.log` forever with no size limit, and repeated runs on default `TICKET-01` append to `TICKET-01.log` forever without triggering file-count rotation.
    - **Fix:** Truncate `_rotated.log` and `<ticket>.log` to last 64 KB on write.
    - **If we skip it:** `.state/archive/` grows without bound over time, breaking `<50KB` bounded storage claim in `README.md`.

13. **`test_prereg_gate_blocks_fresh_prompts_cli` passes for wrong reason** ([tests/test_phase_c.py](file:///Volumes/Dev/lab/unix-primitives/tests/test_phase_c.py#L374-L400))
    - **What this is:** Test copies prompts into `tempfile.TemporaryDirectory()`, sets future `mtime` via `os.utime`, and asserts `run_ab.py` exits 1.
    - **Problem:** `check_preregistration_gate` no longer checks `mtime`; it fails in this test only because `tmp_path` is not a git repo (`git status` fails closed). Deleting commit-timestamp comparison in `run_ab.py` leaves this test green.
    - **Fix:** Run `run_ab.py` CLI against git repo fixture where prompt commit timestamp is newer than `PREREGISTRATION.md`.
    - **If we skip it:** Regressions in CLI pre-registration commit-order check go untested.

14. **Test suite fails 43 tests when host `~/.gitconfig` has external `[include]` or GPG signing** ([tests/conftest.py](file:///Volumes/Dev/lab/unix-primitives/tests/conftest.py#L14-L19))
    - **What this is:** `tmp_ws` fixture and `test_prereg_gate` run `git init` and `git commit` without isolating global git config.
    - **Problem:** `git` inherits user's `~/.gitconfig`; when `~/.gitconfig` includes external paths (e.g., `~/.gitconfigs/...` blocked by sandbox) or enables `commit.gpgsign`, `git init`/`git commit` exits 128 and fails 43 of 94 tests.
    - **Fix:** Set `monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")` and `monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")` in `tmp_ws` and `test_prereg_gate`.
    - **If we skip it:** `pytest` fails out-of-the-box on machines with custom git includes, sandboxes, or GPG commit signing.

### Nice to have

15. **Dead parameters, keys, branches, and redundant `git ls-files` subprocess** ([state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L268), [state_manager.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/state_manager.py#L484-L494), [unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L303), [unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L448), [unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L939))
    - **What this is:** `init_workspace` has unused `governance: Optional[str] = None` parameter, and `verify_gate` runs `git ls-files --error-unmatch` right after `git status --porcelain`. `scan_text` has `strip_fm` parameter, `classify_file_suitability` returns `"rel_path"` key, and `main` checks `cmd in ("scan", None)`.
    - **Problem:** Nothing passes `governance` or `strip_fm=False`; nothing reads `suit["rel_path"]`; `cmd` is never `None` at that branch. `git status --porcelain --ignored -- .unix-primitives` catches modified, deleted, untracked, and gitignored `.unix-primitives` in one subprocess instead of two.
    - **Fix:** Delete `governance` and `strip_fm` parameters, `"rel_path"` key, `None` from `cmd` check, and second `subprocess.run(["git", "ls-files", ...])` block (-16 lines).
    - **If we skip it:** Extra subprocess spawn on every `verify` call and 16 dead lines.

16. **Pre-compile regexes in `PATTERNS` once at import** ([unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L20-L265), [unix_primitives.py](file:///Volumes/Dev/lab/unix-primitives/skills/unix-primitives/scripts/unix_primitives.py#L316))
    - **What this is:** `scan_text` calls `re.finditer(p["regex"], body)` across 17 large regex strings per scanned file.
    - **Problem:** Looking up 17 raw regex strings in `re._cache` on every file scan hashes long pattern strings repeatedly during directory scans.
    - **Fix:** Store `re.compile(...)` in each `PATTERNS` entry at module load and call `p["regex"].finditer(body)`.
    - **If we skip it:** Small repeated cache-lookup overhead on multi-file scans.

### Already fixed (uncommitted, regression test each)

- **F1. Pre-push hook blocked forever after `/unix-clean`** (`state_manager.py` `HOOK_TEMPLATE`): hook ran `verify` whenever `.state/` existed; `clean` keeps dir but deletes `40_impl_green.md`. Now gated on `.state/10_ticket.md`. Test: `test_hook_passes_after_clean`.
- **F2. Eval timeout left agent running** (`eval/run_ab.py`): `subprocess.run(shell=True, timeout=)` killed only shell; compound `AGENT_CMD` agent kept editing sandbox during `check.sh`. Now `Popen(start_new_session=True)` + `os.killpg(SIGKILL)`. Test: `test_timeout_kills_whole_agent_process_group`.
- **F3. Newline in header value overwrote read-only `Ticket-ID`** (`write_headers`, `init`, `stamp --next-action`): new `reject_newlines()`. Remaining gaps tracked in #6. Test: `test_header_newline_rejected`.
- **F4. `verify` passed without running command when `.unix-primitives` lacked parsed `Verify-Command`** (e.g. leading `# comment` line): now exits 1. Related hole tracked in #10. Test: `test_verify_fails_when_config_lacks_command`.
- **F5. Archive rotation deleted logs before writing `_rotated.log`**: now writes first, deletes after. Size growth tracked in #12. No test.
- **F6. `unix_primitives.py delta` exited 0 on missing file**: now stderr + exit 1. Test: `test_delta_missing_file_exits_nonzero`.

Verdict: Fix 1–6 first (`run_ab.py` template/prereg bugs and `state_manager.py` lock/Makefile/header safety), then 7–14.
Lean: -254 lines, -0 dependencies possible.
Not checked: Live multi-model LLM execution in `eval/run_ab.py` (requires external `AGENT_CMD` API keys; verified all 94 tests and dry-run matrix locally). Findings #9, #13, #14 not reproduced; #11 based on SKILL.md read by one auditor only.
