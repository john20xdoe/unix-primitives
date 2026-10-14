import os
import shutil
import subprocess
import time
from pathlib import Path
import pytest


def test_init_refuses_when_active(tmp_ws, sm):
    # Initialize first ticket
    sm.init_workspace(str(tmp_ws), "TICKET-01", "First task")
    ticket_file = tmp_ws / ".state" / "10_ticket.md"
    assert ticket_file.exists()

    # Second init without force should fail
    with pytest.raises(SystemExit) as exc_info:
        sm.init_workspace(str(tmp_ws), "TICKET-02", "Second task", force=False)
    assert exc_info.value.code == 1

    # Verify first ticket still active
    content = ticket_file.read_text(encoding="utf-8")
    assert "TICKET-01" in content


def test_init_force_archives_then_resets(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "First task")
    # Stamp a milestone so there is data to archive
    sm.stamp_milestone(str(tmp_ws), "plan", "My Plan", "next")

    # Second init with force should succeed
    sm.init_workspace(str(tmp_ws), "TICKET-02", "Second task", force=True)

    # Verify archive exists
    archive_file = tmp_ws / ".state" / "archive" / "TICKET-01.log"
    assert archive_file.exists()
    arch_content = archive_file.read_text(encoding="utf-8")
    assert "TICKET-01" in arch_content

    # Verify active ticket is now TICKET-02
    ticket_file = tmp_ws / ".state" / "10_ticket.md"
    assert "TICKET-02" in ticket_file.read_text(encoding="utf-8")


def test_archive_appends_across_two_cleans(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "First task")
    sm.stamp_milestone(str(tmp_ws), "plan", "Plan Version 1", "next")
    sm.clean_active_latches(str(tmp_ws), archive=True)

    # Re-init same ticket and stamp again
    sm.init_workspace(str(tmp_ws), "TICKET-01", "First task", force=True)
    sm.stamp_milestone(str(tmp_ws), "plan", "Plan Version 2", "next")
    sm.clean_active_latches(str(tmp_ws), archive=True)

    archive_file = tmp_ws / ".state" / "archive" / "TICKET-01.log"
    assert archive_file.exists()
    content = archive_file.read_text(encoding="utf-8")
    assert "Plan Version 1" in content
    assert "Plan Version 2" in content
    assert content.count("=== ARCHIVED") >= 2


def test_ticket_id_path_traversal_blocked(tmp_ws, sm):
    evil_id = "../../evil"
    sm.init_workspace(str(tmp_ws), evil_id, "Path traversal attempt", force=True)
    sm.clean_active_latches(str(tmp_ws), archive=True)

    # Must NOT create ../../evil.log outside .state/archive
    evil_path = tmp_ws.parent / "evil.log"
    assert not evil_path.exists()

    archive_dir = tmp_ws / ".state" / "archive"
    assert archive_dir.exists()
    log_files = list(archive_dir.glob("*.log"))
    assert len(log_files) == 1
    assert "evil" in log_files[0].name


def test_hook_preserves_existing(tmp_ws, sm):
    hooks_dir = tmp_ws / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing_hook = hooks_dir / "pre-push"
    existing_hook.write_text("#!/bin/sh\necho 'custom user hook'\nexit 0\n", encoding="utf-8")
    existing_hook.chmod(0o755)

    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=False)

    # Backup file should exist
    backup_file = hooks_dir / "pre-push.unix-primitives.bak"
    assert backup_file.exists()
    assert "custom user hook" in backup_file.read_text(encoding="utf-8")

    # Installed hook should contain managed marker
    assert "# unix-primitives-managed-hook" in existing_hook.read_text(encoding="utf-8")


def test_hook_remove_only_if_marker(tmp_ws, sm):
    hooks_dir = tmp_ws / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    existing_hook = hooks_dir / "pre-push"
    existing_hook.write_text("#!/bin/sh\necho 'user hook'\n", encoding="utf-8")
    existing_hook.chmod(0o755)

    with pytest.raises(SystemExit) as exc_info:
        sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=True)
    assert exc_info.value.code == 1
    assert existing_hook.exists()


def test_hook_remove_restores_backup(tmp_ws, sm):
    hooks_dir = tmp_ws / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    user_hook = hooks_dir / "pre-push"
    user_hook.write_text("#!/bin/sh\necho 'original user hook'\n", encoding="utf-8")
    user_hook.chmod(0o755)

    # Install
    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=False)
    assert (hooks_dir / "pre-push.unix-primitives.bak").exists()

    # Remove
    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=True)
    assert not (hooks_dir / "pre-push.unix-primitives.bak").exists()
    assert user_hook.exists()
    assert "original user hook" in user_hook.read_text(encoding="utf-8")


def test_hook_respects_core_hookspath(tmp_ws, sm):
    custom_hooks = tmp_ws / "custom-hooks"
    custom_hooks.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "config", "core.hooksPath", "custom-hooks"], cwd=str(tmp_ws), check=True)

    sm.manage_hook(str(tmp_ws), hook_type="pre-push", remove=False)
    assert (custom_hooks / "pre-push").exists()


def test_install_script_safety(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    install_sh = repo_root / "install.sh"
    fake_home = tmp_path / "home"
    target_dir = fake_home / ".gemini" / "config" / "skills"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Create a real directory that shouldn't be wiped
    existing_skill = target_dir / "unix-primitives"
    existing_skill.mkdir(parents=True, exist_ok=True)
    canary = existing_skill / "canary.txt"
    canary.write_text("precious user data", encoding="utf-8")

    # Run without --force: must refuse / preserve
    res = subprocess.run(
        ["bash", str(install_sh), "--symlink"],
        env={**os.environ, "HOME": str(fake_home)},
        capture_output=True,
        text=True
    )
    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "precious user data"

    # Run with --force: backup must exist
    res_force = subprocess.run(
        ["bash", str(install_sh), "--symlink", "--force"],
        env={**os.environ, "HOME": str(fake_home)},
        capture_output=True,
        text=True
    )
    assert res_force.returncode == 0
    bak_dirs = list(target_dir.glob("unix-primitives.bak.*"))
    assert len(bak_dirs) >= 1
    assert (bak_dirs[0] / "canary.txt").read_text(encoding="utf-8") == "precious user data"

    # E6: Test external symlink containing substring skills/unix-primitives
    external_dir = tmp_path / "other" / "skills" / "unix-primitives"
    external_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "unix-primitives").unlink()
    (target_dir / "unix-primitives").symlink_to(external_dir)

    res_ext = subprocess.run(
        ["bash", str(install_sh), "--symlink"],
        env={**os.environ, "HOME": str(fake_home)},
        capture_output=True,
        text=True
    )
    # Without force, external symlink must be preserved
    assert (target_dir / "unix-primitives").resolve() == external_dir.resolve()

    # E7: Test UNIX_PRIMITIVES_TARGET override
    custom_target = tmp_path / "custom_skills"
    res_custom = subprocess.run(
        ["bash", str(install_sh), "--symlink"],
        env={**os.environ, "UNIX_PRIMITIVES_TARGET": str(custom_target)},
        capture_output=True,
        text=True
    )
    assert res_custom.returncode == 0
    assert (custom_target / "unix-primitives").exists()
