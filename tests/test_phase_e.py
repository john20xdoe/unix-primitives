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
