import os
import shutil
import subprocess
import time
from pathlib import Path
import pytest


def test_staleness_uses_latest_slot(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Staleness test")
    ticket_file = tmp_ws / ".state" / "10_ticket.md"
    next_action_file = tmp_ws / ".state" / "99_next_action.md"
    assert ticket_file.exists()

    # Backdate 10_ticket.md and initial pointer by 100 hours
    old_time = time.time() - (100 * 3600)
    os.utime(str(ticket_file), (old_time, old_time))
    if next_action_file.exists():
        os.utime(str(next_action_file), (old_time, old_time))

    # Before stamping plan, check staleness: should be STALE
    info = sm.check_staleness(str(tmp_ws))
    assert info["status"] == "STALE"

    # Now stamp plan today
    sm.stamp_milestone(str(tmp_ws), "plan", "Plan stamped now", "next")

    # With latest slot used, should be ACTIVE
    info_after = sm.check_staleness(str(tmp_ws))
    assert info_after["status"] == "ACTIVE"


def test_stamp_requires_prereq(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Prereq test")
    # Slot 30 requires slot 20
    with pytest.raises(SystemExit) as exc:
        sm.stamp_milestone(str(tmp_ws), "tdd", "TDD content", "next", force=False)
    assert exc.value.code == 1

    # Slot 40 requires slot 30
    sm.stamp_milestone(str(tmp_ws), "plan", "Plan content", "next", force=False)
    with pytest.raises(SystemExit) as exc2:
        sm.stamp_milestone(str(tmp_ws), "impl", "Impl content", "next", force=False)
    assert exc2.value.code == 1


def test_stamp_plan_write_once(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Write once test")
    sm.stamp_milestone(str(tmp_ws), "plan", "Initial plan", "next", force=False)

    # Second stamp on plan without force must fail
    with pytest.raises(SystemExit) as exc:
        sm.stamp_milestone(str(tmp_ws), "plan", "Overwriting plan", "next", force=False)
    assert exc.value.code == 1


def test_stamp_force_overrides(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Force override test")
    # Stamp impl directly with force=True (skipping plan and tdd)
    sm.stamp_milestone(str(tmp_ws), "impl", "Forced impl", "next", force=True)
    impl_file = tmp_ws / ".state" / "40_impl_green.md"
    assert impl_file.exists()


def test_verify_missing_impl_fails(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Verify test")
    with pytest.raises(SystemExit) as exc:
        sm.verify_gate(str(tmp_ws))
    assert exc.value.code == 1


def test_verify_runs_command_and_fails_on_nonzero(tmp_ws, sm):
    # Verify with 'false' command fails
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Verify test", verify_cmd="false", force=True)
    sm.stamp_milestone(str(tmp_ws), "impl", "Impl green", "next", force=True)

    with pytest.raises(SystemExit) as exc:
        sm.verify_gate(str(tmp_ws))
    assert exc.value.code == 1

    # Verify with 'true' command passes
    sm.init_workspace(str(tmp_ws), "TICKET-02", "Verify pass test", verify_cmd="true", force=True)
    sm.stamp_milestone(str(tmp_ws), "impl", "Impl green", "next", force=True)
    res = sm.verify_gate(str(tmp_ws))
    assert res is True or res is None


def test_makefile_ci_gate_from_any_cwd(tmp_ws, sm):
    if not shutil.which("make"):
        pytest.skip("make command not found")
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Makefile cwd test", verify_cmd="true", force=True)
    sm.stamp_milestone(str(tmp_ws), "impl", "Impl green", "next", force=True)

    # Run from root with -f .state/Makefile
    r1 = subprocess.run(["make", "-f", ".state/Makefile", "ci-gate"], cwd=str(tmp_ws), capture_output=True, text=True)
    assert r1.returncode == 0, f"make -f failed: {r1.stderr}"

    # Run from .state with -C .state
    r2 = subprocess.run(["make", "-C", ".state", "ci-gate"], cwd=str(tmp_ws), capture_output=True, text=True)
    assert r2.returncode == 0, f"make -C failed: {r2.stderr}"


def test_gitignore_ignores_all_state(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Gitignore test")
    artifacts_dir = tmp_ws / ".state" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    art_file = artifacts_dir / "x.md"
    art_file.write_text("artifact", encoding="utf-8")

    gov_file = tmp_ws / ".state" / "00_governance.md"
    ticket_file = tmp_ws / ".state" / "10_ticket.md"

    # git check-ignore should report all as ignored
    for f in [gov_file, art_file, ticket_file]:
        r = subprocess.run(["git", "check-ignore", "-q", str(f.relative_to(tmp_ws))], cwd=str(tmp_ws))
        assert r.returncode == 0, f"{f} was not ignored by git"


def test_archive_rotation_caps_files(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-00", "Initial", force=True)
    for i in range(1, 26):
        t_id = f"TICKET-{i:02d}"
        sm.init_workspace(str(tmp_ws), t_id, f"Task {i}", force=True)

    archive_dir = tmp_ws / ".state" / "archive"
    assert archive_dir.exists()
    log_files = [f for f in archive_dir.glob("*.log") if not f.name.startswith("_")]
    assert len(log_files) <= 20
    rotated_file = archive_dir / "_rotated.log"
    assert rotated_file.exists()


def test_init_does_not_touch_agents_dir(tmp_ws, sm):
    # Ensure no .agents directory created by default init
    sm.init_workspace(str(tmp_ws), "TICKET-01", "No agents link", force=True)
    agents_dir = tmp_ws / ".agents"
    assert not agents_dir.exists()


def test_artifact_from_stdin(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Stdin test")
    payload = "A" * (1024 * 1024)  # 1 MB

    # Run state_manager.py artifact via subprocess reading stdin
    script_path = Path(sm.__file__).resolve()
    r = subprocess.run(
        ["python3", str(script_path), "artifact", "--role", "large-output", "--content", "-", "--workspace", str(tmp_ws)],
        input=payload,
        text=True,
        capture_output=True,
        check=True
    )
    art_file = tmp_ws / ".state" / "artifacts" / "large-output.md"
    assert art_file.exists()
    assert payload in art_file.read_text(encoding="utf-8")


def test_locked_write_atomic(tmp_ws, sm):
    test_file = str(tmp_ws / ".state" / "atomic_test.txt")
    payload = "Atomic payload data\n" * 100
    sm._locked_write(test_file, payload, mode="w")

    assert os.path.exists(test_file)
    with open(test_file, "r", encoding="utf-8") as f:
        assert f.read() == payload

    # Ensure no .tmp leftover files
    tmp_files = list((tmp_ws / ".state").glob("*.tmp*"))
    assert len(tmp_files) == 0
