import os
import subprocess
import time
from pathlib import Path
import pytest


def test_hook_reinstall_keeps_old_backup(tmp_ws, sm):
    hooks_dir = tmp_ws / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hooks_dir / "pre-push"
    hook_file.write_text("#!/bin/sh\necho 'v1'\n", encoding="utf-8")
    hook_file.chmod(0o755)

    # First install creates backup
    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=False)
    bak1 = hooks_dir / "pre-push.unix-primitives.bak"
    assert bak1.exists()
    assert "v1" in bak1.read_text(encoding="utf-8")

    # User modifies pre-push to unmanaged hook (e.g. husky)
    time.sleep(0.01)
    hook_file.write_text("#!/bin/sh\necho 'husky'\n", encoding="utf-8")

    # Second install: should rename old backup to .bak.<epoch> and keep husky as .bak
    time.sleep(1.0)
    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=False)
    assert bak1.exists()
    assert "husky" in bak1.read_text(encoding="utf-8")

    rotated_baks = list(hooks_dir.glob("pre-push.unix-primitives.bak.*"))
    assert len(rotated_baks) >= 1
    assert "v1" in rotated_baks[0].read_text(encoding="utf-8")


def test_precommit_message(tmp_ws, sm):
    hooks_dir = tmp_ws / ".git" / "hooks"
    sm.manage_hook(str(tmp_ws), hook_type="pre-commit", remove=False)
    precommit_file = hooks_dir / "pre-commit"
    assert precommit_file.exists()
    content = precommit_file.read_text(encoding="utf-8")
    assert "Fix milestone or run /unix-clean before committing" in content
    assert "Local commits remain safe" not in content


def test_link_agents_quiet_when_noop(tmp_ws, sm, capsys):
    # Workspace without .agents/skills should output nothing
    sm.link_project_agents(str(tmp_ws))
    captured = capsys.readouterr()
    assert "Warning: symlinks in .agents/skills/" not in captured.out
    assert "Auto-linked" not in captured.out


def test_no_lock_litter_in_hooks_dir(tmp_ws, sm):
    hooks_dir = tmp_ws / ".git" / "hooks"
    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=False)
    # Check that no .lock exists inside hooks dir
    assert not (hooks_dir / ".lock").exists()


def test_hook_calls_verify_directly(tmp_ws, sm):
    hooks_dir = tmp_ws / ".git" / "hooks"
    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=False)
    content = (hooks_dir / "pre-push").read_text(encoding="utf-8")
    assert "verify --workspace" in content
    assert "ci-gate" not in content


def test_hook_passes_after_clean(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "T1", "t")
    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=False)
    sm.clean_active_latches(str(tmp_ws), archive=True)
    hook = tmp_ws / ".git" / "hooks" / "pre-push"
    res = subprocess.run([str(hook)], cwd=str(tmp_ws), stdin=subprocess.DEVNULL, capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr


def test_header_newline_rejected(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "T1", "t")
    with pytest.raises(SystemExit):
        sm.update_ticket(str(tmp_ws), "Status", "x\nTicket-ID: evil")
    with pytest.raises(SystemExit):
        sm.init_workspace(str(tmp_ws), "T2", "a\nTicket-ID: evil", force=True)
    headers, _ = sm.read_headers(str(tmp_ws / ".state" / "10_ticket.md"))
    assert headers["Ticket-ID"] == "T1"


def test_verify_fails_when_config_lacks_command(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "T1", "t")
    (tmp_ws / ".unix-primitives").write_text("# gate\nVerify-Command: false\n", encoding="utf-8")
    subprocess.run(["git", "add", ".unix-primitives"], cwd=str(tmp_ws), check=True)
    subprocess.run(["git", "commit", "-qm", "cfg"], cwd=str(tmp_ws), check=True)
    sm.stamp_milestone(str(tmp_ws), "impl", "i", "next", force=True)
    with pytest.raises(SystemExit) as exc:
        sm.verify_gate(str(tmp_ws))
    assert exc.value.code == 1


def test_delta_missing_file_exits_nonzero(tmp_path):
    script = Path(__file__).resolve().parent.parent / "skills" / "unix-primitives" / "scripts" / "unix_primitives.py"
    res = subprocess.run(["python3", str(script), "delta", str(tmp_path / "a"), str(tmp_path / "b")], capture_output=True, text=True)
    assert res.returncode == 1
    assert "not found" in res.stderr
