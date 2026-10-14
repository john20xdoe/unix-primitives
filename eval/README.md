# Empirical A/B Evaluation Harness

Empirical validation harness comparing agent execution reliability between original (natural language) and converted (Unix/CS formalisms) prompt variants.

## Overview

The static **friction score** emitted by `unix_primitives.py` is a linting heuristic measuring pattern frequency against canonical Unix formalisms. It is **not** an empirical measurement of LLM capability or task performance.

This harness provides empirical benchmarking:
1. Executes a matrix of tasks across prompt variants.
2. Runs each cell $N$ times to measure variance.
3. Automatically evaluates outcomes using deterministic acceptance test scripts (`check.sh`).
4. Computes pass rates with a Wilson 95% binomial confidence interval.

## Directory Structure

```text
eval/
├── README.md               # Documentation
├── run_ab.py               # Evaluation driver (Python stdlib only)
├── prompts/                # Prompt variants for comparison
│   ├── original.md         # Baseline natural-language prompt
│   └── converted.md        # Refactored prompt with Unix formalisms
└── tasks/                  # Task test suite
    ├── 01_retry_loop_bait/ # Evaluates circuit breaker behavior under failure
    ├── 02_multistep_build/ # Evaluates multistep build dependency adherence
    └── 03_least_privilege/ # Evaluates file immutability and capability boundaries
```

Each task in `eval/tasks/` contains:
* `task.md`: The task description given to the agent.
* `check.sh`: An executable bash script that exits 0 on success, non-zero on failure.
* Optional fixture files or starter templates.

## Usage

### 1. Dry Run (Verify Test Matrix)

Verify discovered tasks, prompt variants, and planned execution matrix without invoking an LLM:

```bash
python3 eval/run_ab.py --dry-run
```

### 2. Live Execution with Agent CLI

Provide an external agent command via `AGENT_CMD`:

```bash
export AGENT_CMD="my-agent-cli --prompt {prompt_file} --dir {task_dir}"
python3 eval/run_ab.py -n 5
```

Available template variables in `AGENT_CMD`:
* `{prompt_file}`: Path to the combined prompt (variant + task instructions).
* `{task_dir}`: Path to the isolated sandbox directory for the run.
* `{task_name}`: Name of the current task directory.
* `{variant}`: Name of the active prompt variant (e.g. `original`, `converted`).

### 3. Statistical Analysis

The harness computes the binomial success rate and the **Wilson 95% confidence interval**:
$$\text{CI}_{95\%} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
where $z = 1.96$. This accounts for small sample sizes without assuming normality.
