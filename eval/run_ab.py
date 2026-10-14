#!/usr/bin/env python3
"""
run_ab.py - Empirical A/B evaluation harness for prompt variants.

Compares task execution reliability between original (natural language)
and converted (unix primitives) prompt variants across automated task suites.
"""

import sys
import os
import math
import shutil
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple


def wilson_score_interval(successes: int, total: int, z: float = 1.95996) -> Tuple[float, float]:
    """Calculate Wilson score interval (95% CI by default) for a binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z ** 2) / total
    center = (p + (z ** 2) / (2.0 * total)) / denom
    radicand = (p * (1.0 - p) / total) + ((z ** 2) / (4.0 * (total ** 2)))
    margin = (z * math.sqrt(max(0.0, radicand))) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return (lower, upper)


def discover_tasks(tasks_dir: Path) -> List[Path]:
    """Find task directories containing task.md and check.sh."""
    tasks = []
    if not tasks_dir.exists():
        return tasks
    for item in sorted(tasks_dir.iterdir()):
        if item.is_dir() and (item / "task.md").exists() and (item / "check.sh").exists():
            tasks.append(item)
    return tasks


def discover_variants(prompts_dir: Path) -> Dict[str, Path]:
    """Find prompt variants in prompts_dir."""
    variants = {}
    if not prompts_dir.exists():
        return variants
    for item in sorted(prompts_dir.iterdir()):
        if item.is_file() and item.suffix in [".md", ".converted", ".txt"]:
            variants[item.stem] = item
    return variants


def main() -> None:
    parser = argparse.ArgumentParser(description="Run empirical A/B evaluation harness.")
    parser.add_argument("--tasks-dir", default=str(Path(__file__).parent / "tasks"), help="Path to tasks directory")
    parser.add_argument("--prompts-dir", default=str(Path(__file__).parent / "prompts"), help="Path to prompt variants directory")
    parser.add_argument("-n", "--iterations", type=int, default=3, help="Number of iterations per (task, variant) pair")
    parser.add_argument("--timeout", type=int, default=120, help="Per-run timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print planned test matrix and exit 0 without running agent")
    args = parser.parse_args()

    tasks_dir = Path(args.tasks_dir).resolve()
    prompts_dir = Path(args.prompts_dir).resolve()

    tasks = discover_tasks(tasks_dir)
    variants = discover_variants(prompts_dir)

    if not tasks:
        print(f"Error: No valid tasks found in {tasks_dir}. Each task directory must contain 'task.md' and 'check.sh'.", file=sys.stderr)
        sys.exit(1)

    if not variants:
        # Provide default synthetic variants if prompts dir is empty
        variants = {
            "original": prompts_dir / "original.md",
            "converted": prompts_dir / "converted.md"
        }

    total_runs = len(tasks) * len(variants) * args.iterations

    print("=== Empirical Prompt A/B Evaluation Matrix ===")
    print(f"Tasks ({len(tasks)}): {[t.name for t in tasks]}")
    print(f"Variants ({len(variants)}): {list(variants.keys())}")
    print(f"Iterations per cell: {args.iterations}")
    print(f"Total planned runs:  {total_runs}\n")

    print(f"{'Run #':<6} | {'Task':<25} | {'Variant':<15} | {'Iteration'}")
    print("-" * 65)
    run_idx = 1
    for task in tasks:
        for v_name in variants:
            for it in range(1, args.iterations + 1):
                print(f"{run_idx:<6} | {task.name[:25]:<25} | {v_name[:15]:<15} | Run {it}/{args.iterations}")
                run_idx += 1

    if args.dry_run:
        print("\nDry-run mode: Planned matrix displayed successfully. Exiting 0.")
        sys.exit(0)

    agent_cmd = os.environ.get("AGENT_CMD")
    if not agent_cmd:
        print("\nError: Environment variable AGENT_CMD is required to execute runs (e.g. AGENT_CMD=\"my-agent-cli --prompt {prompt_file}\").", file=sys.stderr)
        print("Set AGENT_CMD or run with --dry-run.", file=sys.stderr)
        sys.exit(1)

    results: Dict[str, Dict[str, int]] = {v: {"pass": 0, "fail": 0, "total": 0} for v in variants}

    print("\n=== Executing Evaluation Matrix ===")
    for task in tasks:
        task_prompt = (task / "task.md").read_text(encoding="utf-8")
        check_script = task / "check.sh"

        for v_name, v_path in variants.items():
            variant_prompt = v_path.read_text(encoding="utf-8") if v_path.exists() else ""

            for it in range(1, args.iterations + 1):
                with tempfile.TemporaryDirectory(prefix="eval_run_") as tmpdir:
                    sandbox = Path(tmpdir)
                    # Copy task files into sandbox
                    for item in task.iterdir():
                        if item.name not in ["task.md", "check.sh"]:
                            if item.is_dir():
                                shutil.copytree(item, sandbox / item.name)
                            else:
                                shutil.copy2(item, sandbox / item.name)

                    combined_prompt = f"{variant_prompt}\n\nTask:\n{task_prompt}"
                    prompt_file = sandbox / ".prompt_input.txt"
                    prompt_file.write_text(combined_prompt, encoding="utf-8")

                    formatted_cmd = agent_cmd.format(
                        prompt_file=str(prompt_file),
                        task_dir=str(sandbox),
                        task_name=task.name,
                        variant=v_name
                    )

                    try:
                        subprocess.run(
                            formatted_cmd,
                            shell=True,
                            cwd=str(sandbox),
                            timeout=args.timeout,
                            capture_output=True,
                            text=True
                        )
                    except subprocess.TimeoutExpired:
                        pass

                    # Run check.sh in sandbox
                    try:
                        res = subprocess.run(
                            ["bash", str(check_script)],
                            cwd=str(sandbox),
                            timeout=30,
                            capture_output=True,
                            text=True
                        )
                        passed = (res.returncode == 0)
                    except Exception:
                        passed = False

                    status_str = "PASS" if passed else "FAIL"
                    print(f"[{status_str}] Task: {task.name} | Variant: {v_name} | Iteration {it}/{args.iterations}")

                    results[v_name]["total"] += 1
                    if passed:
                        results[v_name]["pass"] += 1
                    else:
                        results[v_name]["fail"] += 1

    print("\n=== Evaluation Results Summary ===")
    print(f"{'Variant':<15} | {'Passed':<8} | {'Total':<6} | {'Success Rate':<14} | {'95% Wilson CI'}")
    print("-" * 65)

    for v_name, r in results.items():
        total = r["total"]
        passed = r["pass"]
        rate = (passed / total * 100.0) if total > 0 else 0.0
        ci_low, ci_high = wilson_score_interval(passed, total)
        print(f"{v_name:<15} | {passed:<8} | {total:<6} | {rate:>6.1f}%       | [{ci_low * 100:.1f}%, {ci_high * 100:.1f}%]")


if __name__ == "__main__":
    main()
