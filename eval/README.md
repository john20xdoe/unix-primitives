# Empirical Evaluation Harness

Empirical validation harness comparing agent execution reliability across 4 prompt arms and host enforcement mechanisms.

## Overview

The static **friction score** emitted by `unix_primitives.py` is a linting heuristic measuring pattern frequency against canonical Unix formalisms. It is **not** an empirical measurement of LLM capability or task performance.

This harness provides empirical benchmarking:
1. Executes a matrix of tasks across 4 distinct arms.
2. Runs each cell $N \ge 20$ times to measure variance.
3. Automatically evaluates outcomes using deterministic acceptance test scripts (`check.sh`).
4. Computes pass rates with a Wilson 95% binomial confidence interval and two-sided Fisher exact tests.
5. Records per-run execution logs in newline-delimited JSON (`results/*.jsonl`).

## The Four Arms & Scientific Interpretation

| Arm | Description | Purpose / Comparison |
|---|---|---|
| `prose` | Natural language prose instructions | Baseline ambiguity |
| `bespoke` | Invented checklist / custom DSL | Isolates structure: $\text{bespoke} - \text{prose}$ measures benefit of formal structure over prose |
| `canonical` | Canonical Unix/CS primitives | Isolates familiarity: $\text{canonical} - \text{bespoke}$ measures pre-training weight gravity |
| `host` | Host-enforced physical latches (Level 2) | Isolates physical enforcement: $\text{host} - \text{canonical}$ measures Level 2 machine gates over Level 1 prompt-only |

## Directory Structure

```text
eval/
├── README.md               # Documentation
├── PREREGISTRATION.md      # Pre-registered study hypotheses & protocol
├── run_ab.py               # Evaluation driver (Python stdlib only)
├── results/                # JSONL per-run records
├── prompts/                # 4 arms per task
│   ├── 01_retry_loop_bait/
│   │   ├── prose.md
│   │   ├── bespoke.md
│   │   ├── canonical.md
│   │   └── host.md
│   ├── 02_multistep_build/ ...
│   ├── 03_least_privilege/ ...
│   └── 04_multifile_atomic/ ...
└── tasks/                  # Task test suites
    ├── 01_retry_loop_bait/ # Evaluates circuit breaker behavior under failure
    ├── 02_multistep_build/ # Evaluates multistep build dependency order via mtimes
    ├── 03_least_privilege/ # Evaluates file immutability under whitespace distractor
    └── 04_multifile_atomic/# Evaluates 2PC atomic rollback across multiple modules
```

Each task in `eval/tasks/` contains:
* `task.md`: Neutral task instructions with no constraint leakage.
* `check.sh`: Acceptance test script (exit 0 on success, non-zero on failure).
* Fixture files and execution targets.

## Usage

### 1. Dry Run (Verify Test Matrix)

Verify discovered tasks, prompt arms, and planned execution matrix without invoking an LLM:

```bash
python3 eval/run_ab.py --dry-run
```

### 2. Live Execution with Agent CLI

Provide an external agent command via `AGENT_CMD`:

```bash
export AGENT_CMD="my-agent-cli --prompt {prompt_file} --dir {task_dir}"
python3 eval/run_ab.py -n 20 --model gpt-4o --seed 42
```

#### Example: Antigravity

Run evaluations using the `agy` CLI in non-interactive print mode:

```bash
export AGENT_CMD='bash -c '\''agy -p "$(<"$1")" --dangerously-skip-permissions'\'' _ {prompt_file}'
python3 eval/run_ab.py -n 20 --model gpt-4o --seed 42
```

Available template variables in `AGENT_CMD`:
* `{prompt_file}`: Path to the combined prompt (variant + task instructions).
* `{task_dir}`: Path to the isolated sandbox directory for the run.
* `{task_name}`: Name of the current task directory.
* `{variant}`: Name of the active prompt arm (`prose`, `bespoke`, `canonical`, `host`).

### 3. Statistical Analysis

The harness computes:
1. **Wilson 95% Confidence Interval**:
   $$\text{CI}_{0.95} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
   where $z = 1.95996$.
2. **Two-Sided Fisher's Exact Test**:
   Exact hypergeometric probability on $2 \times 2$ contingency tables testing pairwise significance between arms ($p < 0.05$).

### 4. Pre-Registration Gate

To prevent p-hacking and post-hoc prompt tweaking, `run_ab.py` verifies that `eval/PREREGISTRATION.md` exists and was registered after or concurrently with prompt updates. Pass `--no-prereg` to bypass this check in development.
