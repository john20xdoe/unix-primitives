#!/usr/bin/env python3
"""
run_ab.py - Empirical evaluation harness for prompt arms and host enforcement.

Compares task execution reliability across four arms:
1. prose: Unstructured natural language baseline
2. bespoke: Invented domain-specific language / checklist
3. canonical: Canonical Unix & CS primitives (pre-training gravity)
4. host: Level 2 host-enforced physical latches
"""

import sys
import os
import re
import math
import json
import time
import shutil
import random
import argparse
import datetime
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional


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


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """
    Two-sided Fisher exact test for a 2x2 contingency table using stdlib math.comb.
    Table:
        [[a, b],
         [c, d]]
    """
    n1 = a + b
    n2 = c + d
    k = a + c
    N = n1 + n2
    if N == 0 or n1 == 0 or n2 == 0:
        return 1.0

    denom = math.comb(N, n1)
    min_x = max(0, k - n2)
    max_x = min(k, n1)

    probs = {}
    for x in range(min_x, max_x + 1):
        num = math.comb(k, x) * math.comb(N - k, n1 - x)
        probs[x] = num / denom

    p_obs = probs.get(a, 0.0)
    p_val = sum(p for p in probs.values() if p <= p_obs * (1.0 + 1e-9) or p <= p_obs + 1e-12)
    return min(1.0, float(p_val))


def check_preregistration_gate(prompts_dir: Path, prereg_file: Path) -> bool:
    """
    Check that pre-registration file exists, is non-empty, and has mtime
    greater than or equal to all prompt files in prompts_dir.
    """
    if not prereg_file.exists() or prereg_file.stat().st_size == 0:
        return False

    prereg_mtime = prereg_file.stat().st_mtime
    if prompts_dir.exists():
        for p in prompts_dir.rglob("*.md"):
            if p.is_file() and p.stat().st_mtime > prereg_mtime:
                return False

    return True


def discover_tasks(tasks_dir: Path) -> List[Path]:
    """Find task directories containing task.md and check.sh."""
    tasks = []
    if not tasks_dir.exists():
        return tasks
    for item in sorted(tasks_dir.iterdir()):
        if item.is_dir() and (item / "task.md").exists() and (item / "check.sh").exists():
            tasks.append(item)
    return tasks


def discover_task_arms(prompts_dir: Path, tasks: List[Path]) -> Dict[str, Dict[str, Path]]:
    """
    Discover prompt arms for each task from prompts_dir / task.name / <arm>.md.
    """
    task_arms: Dict[str, Dict[str, Path]] = {}
    if not prompts_dir.exists():
        return task_arms

    for task in tasks:
        task_prompts_dir = prompts_dir / task.name
        arms: Dict[str, Path] = {}
        if task_prompts_dir.is_dir():
            for f in sorted(task_prompts_dir.iterdir()):
                if f.is_file() and f.suffix in [".md", ".converted", ".txt"]:
                    arms[f.stem] = f
        if arms:
            task_arms[task.name] = arms

    return task_arms


def _print_summary_table_and_fishers(title: str, stats_dict: Dict[str, Dict[str, int]]) -> None:
    print(f"\n=== {title} ===")
    print(f"{'Arm':<15} | {'Passed':<8} | {'Total':<6} | {'Success Rate':<14} | {'95% Wilson CI':<18} | {'Timeouts':<9} | {'Agent Errors'}")
    print("-" * 88)

    for arm_name, r in stats_dict.items():
        total = r["total"]
        passed = r["pass"]
        timeouts = r.get("timeouts", 0)
        agent_errors = r.get("agent_errors", 0)
        rate = (passed / total * 100.0) if total > 0 else 0.0
        ci_low, ci_high = wilson_score_interval(passed, total)
        print(f"{arm_name:<15} | {passed:<8} | {total:<6} | {rate:>6.1f}%       | [{ci_low * 100:>5.1f}%, {ci_high * 100:>5.1f}%]   | {timeouts:<9} | {agent_errors}")

    print("\nPairwise Fisher's Exact Tests:")
    comparisons = [
        ("canonical", "bespoke", "H1: Familiarity / Pre-training gravity (canonical vs bespoke)"),
        ("bespoke", "prose", "H2: Structure over ambiguity (bespoke vs prose)"),
        ("host", "canonical", "H3: Level 2 host enforcement over Level 1 prompt (host vs canonical)")
    ]

    for arm1, arm2, desc in comparisons:
        if arm1 in stats_dict and arm2 in stats_dict:
            s1, f1 = stats_dict[arm1]["pass"], stats_dict[arm1]["fail"]
            s2, f2 = stats_dict[arm2]["pass"], stats_dict[arm2]["fail"]
            p_val = fisher_exact(s1, f1, s2, f2)
            sig_marker = "***" if p_val < 0.001 else ("**" if p_val < 0.01 else ("*" if p_val < 0.05 else "n.s."))
            print(f"  {desc}: p = {p_val:.4f} ({sig_marker})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run empirical evaluation harness across prompt arms.")
    parser.add_argument("--tasks-dir", default=str(Path(__file__).parent / "tasks"), help="Path to tasks directory")
    parser.add_argument("--prompts-dir", default=str(Path(__file__).parent / "prompts"), help="Path to prompt arms directory")
    parser.add_argument("--results-dir", default=str(Path(__file__).parent / "results"), help="Path to results directory")
    parser.add_argument("-n", "--iterations", type=int, default=20, help="Number of iterations per (task, arm) cell (default: 20)")
    parser.add_argument("--timeout", type=int, default=180, help="Per-run timeout in seconds (default: 180)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible execution ordering")
    parser.add_argument("--model", default="default", help="Model label identifier for JSONL logs")
    parser.add_argument("--arms", default="prose,bespoke,canonical,host", help="Required prompt arms, comma-separated (default: prose,bespoke,canonical,host)")
    parser.add_argument("--no-prereg", action="store_true", help="Bypass pre-registration gate validation")
    parser.add_argument("--dry-run", action="store_true", help="Print planned test matrix and exit 0 without running agent")
    args = parser.parse_args()

    tasks_dir = Path(args.tasks_dir).resolve()
    prompts_dir = Path(args.prompts_dir).resolve()
    results_dir = Path(args.results_dir).resolve()
    prereg_file = Path(__file__).parent / "PREREGISTRATION.md"

    # Pre-registration gate
    prereg_bypassed = False
    if args.no_prereg:
        if not args.dry_run:
            print("WARNING: pre-registration gate bypassed (--no-prereg)", file=sys.stderr)
        prereg_bypassed = True
    else:
        if not check_preregistration_gate(prompts_dir, prereg_file):
            print(
                "Error: Pre-registration gate failed. PREREGISTRATION.md must exist, be non-empty, "
                "and have mtime >= all prompt files in prompts/.\n"
                "Register hypotheses first or pass --no-prereg to bypass during development.",
                file=sys.stderr
            )
            sys.exit(1)

    tasks = discover_tasks(tasks_dir)
    if not tasks:
        print(f"Error: No valid tasks found in {tasks_dir}. Each task directory must contain 'task.md' and 'check.sh'.", file=sys.stderr)
        sys.exit(1)

    task_arms = discover_task_arms(prompts_dir, tasks)
    required_arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    # Validate that every discovered task has all required arms
    for task in tasks:
        arms = task_arms.get(task.name, {})
        missing = [a for a in required_arms if a not in arms]
        if missing:
            print(f"Error: Task '{task.name}' missing required arms: {missing}", file=sys.stderr)
            sys.exit(1)

    all_arm_names = sorted({arm for arms in task_arms.values() for arm in arms.keys()})

    # Build planned runs schedule
    planned_runs = [
        (task, arm_name, task_arms[task.name][arm_name], it)
        for task in tasks
        for arm_name in sorted(task_arms.get(task.name, {}).keys())
        for it in range(1, args.iterations + 1)
    ]
    if args.seed is not None:
        rng = random.Random(args.seed)
        rng.shuffle(planned_runs)

    print("=== Empirical Evaluation Matrix ===")
    print(f"Tasks ({len(tasks)}): {[t.name for t in tasks]}")
    print(f"Discovered Arms ({len(all_arm_names)}): {all_arm_names}")
    print(f"Iterations per cell: {args.iterations}")
    print(f"Model identifier:    {args.model}")
    print(f"Total planned runs:  {len(planned_runs)}\n")

    print(f"{'Run #':<6} | {'Task':<25} | {'Arm':<15} | {'Iteration'}")
    print("-" * 65)
    for run_idx, (task, arm_name, arm_path, it) in enumerate(planned_runs, start=1):
        print(f"{run_idx:<6} | {task.name[:25]:<25} | {arm_name[:15]:<15} | Run {it}/{args.iterations}")

    if args.dry_run:
        print("\nDry-run mode: Planned matrix displayed successfully. Exiting 0.")
        sys.exit(0)

    agent_cmd = os.environ.get("AGENT_CMD")
    if not agent_cmd:
        print("\nError: Environment variable AGENT_CMD is required to execute runs (e.g. AGENT_CMD=\"my-agent-cli --prompt {prompt_file}\").", file=sys.stderr)
        print("Set AGENT_CMD or run with --dry-run.", file=sys.stderr)
        sys.exit(1)

    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    jsonl_path = results_dir / f"eval_{timestamp_str}.jsonl"

    task_cell_stats: Dict[Tuple[str, str, str], Dict[str, int]] = {}
    for task in tasks:
        for arm in all_arm_names:
            task_cell_stats[(task.name, args.model, arm)] = {"pass": 0, "fail": 0, "total": 0, "timeouts": 0, "agent_errors": 0}

    pooled_stats: Dict[str, Dict[str, int]] = {arm: {"pass": 0, "fail": 0, "total": 0, "timeouts": 0, "agent_errors": 0} for arm in all_arm_names}

    print("\n=== Executing Evaluation Matrix ===")
    with open(jsonl_path, "a", encoding="utf-8") as jsonl_file:
        for run_idx, (task, arm_name, arm_path, it) in enumerate(planned_runs, start=1):
            task_prompt = (task / "task.md").read_text(encoding="utf-8")
            check_script = task / "check.sh"
            arm_prompt = arm_path.read_text(encoding="utf-8") if arm_path.exists() else ""

            t0 = time.time()
            with tempfile.TemporaryDirectory(prefix="eval_run_") as tmpdir:
                sandbox = Path(tmpdir)

                # Copy task files into sandbox, isolating host-specific files from non-host arms
                for item in task.iterdir():
                    if item.name in ["task.md", "check.sh", "host_overlay"]:
                        continue
                    if arm_name != "host" and item.name in ["Makefile", "transaction.sh"]:
                        continue
                    if item.is_dir():
                        shutil.copytree(item, sandbox / item.name)
                    else:
                        shutil.copy2(item, sandbox / item.name)

                # Apply host overlay if host arm
                if arm_name == "host" and (task / "host_overlay").is_dir():
                    for item in (task / "host_overlay").iterdir():
                        if item.is_dir():
                            if (sandbox / item.name).exists():
                                shutil.rmtree(sandbox / item.name)
                            shutil.copytree(item, sandbox / item.name)
                        else:
                            shutil.copy2(item, sandbox / item.name)

                # Host security latches: permissions on protected data
                prot_file = sandbox / "data" / "protected.txt"
                data_dir = sandbox / "data"
                need_restore_perms = False
                if arm_name == "host" and prot_file.exists():
                    os.chmod(str(prot_file), 0o444)
                    os.chmod(str(data_dir), 0o555)
                    need_restore_perms = True

                try:
                    combined_prompt = f"{arm_prompt}\n\nTask:\n{task_prompt}"
                    prompt_file = sandbox / ".prompt_input.txt"
                    prompt_file.write_text(combined_prompt, encoding="utf-8")

                    formatted_cmd = agent_cmd.format(
                        model=args.model,
                        prompt_file=str(prompt_file),
                        task_dir=str(sandbox),
                        task_name=task.name,
                        variant=arm_name
                    )

                    agent_exit = 0
                    timed_out = False
                    agent_out = ""
                    agent_err = ""
                    try:
                        agent_res = subprocess.run(
                            formatted_cmd,
                            shell=True,
                            cwd=str(sandbox),
                            timeout=args.timeout,
                            capture_output=True,
                            text=True
                        )
                        agent_exit = agent_res.returncode
                        agent_out = agent_res.stdout or ""
                        agent_err = agent_res.stderr or ""
                    except subprocess.TimeoutExpired:
                        agent_exit = 124
                        timed_out = True

                    host_chmod_attempt = False
                    if arm_name == "host":
                        if re.search(r"\bchmod\b", agent_out + " " + agent_err):
                            host_chmod_attempt = True

                    # Run check.sh in sandbox
                    check_exit = 0
                    try:
                        res = subprocess.run(
                            ["bash", str(check_script)],
                            cwd=str(sandbox),
                            timeout=30,
                            capture_output=True,
                            text=True
                        )
                        check_exit = res.returncode
                        passed = (check_exit == 0)
                    except subprocess.TimeoutExpired:
                        check_exit = 124
                        passed = False
                    except Exception:
                        check_exit = 1
                        passed = False

                    duration_s = round(time.time() - t0, 3)
                    status_str = "PASS" if passed else "FAIL"
                    print(f"[{status_str}] Task: {task.name:<20} | Arm: {arm_name:<10} | Iteration {it}/{args.iterations}")

                    key = (task.name, args.model, arm_name)
                    task_cell_stats[key]["total"] += 1
                    if passed:
                        task_cell_stats[key]["pass"] += 1
                    else:
                        task_cell_stats[key]["fail"] += 1
                    if timed_out:
                        task_cell_stats[key]["timeouts"] += 1
                    if agent_exit != 0 and not timed_out:
                        task_cell_stats[key]["agent_errors"] += 1

                    pooled_stats[arm_name]["total"] += 1
                    if passed:
                        pooled_stats[arm_name]["pass"] += 1
                    else:
                        pooled_stats[arm_name]["fail"] += 1
                    if timed_out:
                        pooled_stats[arm_name]["timeouts"] += 1
                    if agent_exit != 0 and not timed_out:
                        pooled_stats[arm_name]["agent_errors"] += 1

                    record = {
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "task": task.name,
                        "arm": arm_name,
                        "model": args.model,
                        "iteration": it,
                        "passed": passed,
                        "agent_exit": agent_exit,
                        "timed_out": timed_out,
                        "check_exit": check_exit,
                        "duration_s": duration_s,
                        "prereg_bypassed": prereg_bypassed,
                        "host_chmod_attempt": host_chmod_attempt
                    }
                    jsonl_file.write(json.dumps(record) + "\n")
                    jsonl_file.flush()
                finally:
                    if need_restore_perms:
                        try:
                            os.chmod(str(data_dir), 0o755)
                            os.chmod(str(prot_file), 0o644)
                        except Exception:
                            pass

    # Per (task, model) reporting
    for task in tasks:
        cell_dict = {arm: task_cell_stats[(task.name, args.model, arm)] for arm in all_arm_names}
        _print_summary_table_and_fishers(f"Results: Task '{task.name}' | Model '{args.model}'", cell_dict)

    # Pooled reporting
    _print_summary_table_and_fishers(f"Pooled Results Across All Tasks | Model '{args.model}'", pooled_stats)

    if prereg_bypassed:
        print("\nWARNING: pre-registration gate was bypassed for this run (--no-prereg).", file=sys.stderr)

    print(f"\nResults log written to: {jsonl_path}")


if __name__ == "__main__":
    main()
