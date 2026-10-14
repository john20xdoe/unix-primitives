import os
import subprocess
import time
from pathlib import Path
import pytest


def test_stamp_rejects_governance_slot(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Gov reject test")
    with pytest.raises(SystemExit) as exc:
        sm.stamp_milestone(str(tmp_ws), "0", "Gov content", "next", force=True)
    assert exc.value.code == 1


def test_stamp_rejects_next_action_slot(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Next action reject test")
    with pytest.raises(SystemExit) as exc:
        sm.stamp_milestone(str(tmp_ws), "99", "Next content", "next", force=True)
    assert exc.value.code == 1


def test_stamp_rejects_ticket_slot(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Ticket reject test")
    with pytest.raises(SystemExit) as exc:
        sm.stamp_milestone(str(tmp_ws), "ticket", "Ticket content", "next", force=True)
    assert exc.value.code == 1
    with pytest.raises(SystemExit) as exc2:
        sm.stamp_milestone(str(tmp_ws), "10", "Ticket content", "next", force=True)
    assert exc2.value.code == 1


def test_headers_roundtrip(tmp_path, sm):
    test_file = tmp_path / "headers_test.txt"
    headers = {"Ticket-ID": "T-100", "Title": "Header Test", "Verify-Command": "make test"}
    body = "## Body\nSome body text here.\n"
    sm.write_headers(str(test_file), headers, body)

    read_h, read_b = sm.read_headers(str(test_file))
    assert read_h["Ticket-ID"] == "T-100"
    assert read_h["Title"] == "Header Test"
    assert read_h["Verify-Command"] == "make test"
    assert "Some body text here." in read_b


def test_update_ticket_preserves_other_headers(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Initial title")
    ticket_file = tmp_ws / ".state" / "10_ticket.md"
    orig_h, _ = sm.read_headers(str(ticket_file))
    assert orig_h["Ticket-ID"] == "TICKET-01"
    assert "Created" in orig_h

    sm.update_ticket(str(tmp_ws), "Title", "Updated title")
    new_h, new_b = sm.read_headers(str(ticket_file))
    assert new_h["Title"] == "Updated title"
    assert new_h["Ticket-ID"] == "TICKET-01"
    assert new_h["Created"] == orig_h["Created"]


def test_update_ticket_refuses_ticket_id(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Initial title")
    with pytest.raises(SystemExit) as exc:
        sm.update_ticket(str(tmp_ws), "Ticket-ID", "TICKET-02")
    assert exc.value.code == 1
    with pytest.raises(SystemExit) as exc2:
        sm.update_ticket(str(tmp_ws), "Created", "2026-01-01T00:00:00Z")
    assert exc2.value.code == 1


def test_restamp_lower_invalidates_higher(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Invalidation test")
    sm.stamp_milestone(str(tmp_ws), "plan", "Plan content", "next")
    sm.stamp_milestone(str(tmp_ws), "tdd", "TDD content", "next")
    sm.stamp_milestone(str(tmp_ws), "impl", "Impl content", "next")

    plan_file = tmp_ws / ".state" / "20_plan.md"
    tdd_file = tmp_ws / ".state" / "30_tdd_red.md"
    impl_file = tmp_ws / ".state" / "40_impl_green.md"
    assert plan_file.exists()
    assert tdd_file.exists()
    assert impl_file.exists()

    # Re-stamp tdd with force: should invalidate slot 40 (impl)
    time.sleep(0.01)
    sm.stamp_milestone(str(tmp_ws), "tdd", "TDD content 2", "next", force=True)

    assert plan_file.exists()
    assert tdd_file.exists()
    assert not impl_file.exists()


def test_verify_fails_on_mtime_inversion(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Mtime inversion test")
    sm.stamp_milestone(str(tmp_ws), "plan", "Plan content", "next")
    sm.stamp_milestone(str(tmp_ws), "tdd", "TDD content", "next")
    sm.stamp_milestone(str(tmp_ws), "impl", "Impl content", "next")

    plan_file = tmp_ws / ".state" / "20_plan.md"
    tdd_file = tmp_ws / ".state" / "30_tdd_red.md"

    # Invert mtime: make tdd older than plan
    now = time.time()
    os.utime(str(plan_file), (now, now))
    os.utime(str(tdd_file), (now - 100, now - 100))

    with pytest.raises(SystemExit) as exc:
        sm.verify_gate(str(tmp_ws))
    assert exc.value.code == 1


def test_verify_reads_repo_config(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Repo config test", verify_cmd="true")
    repo_cfg = tmp_ws / ".unix-primitives"
    assert repo_cfg.exists()
    assert "Verify-Command: true" in repo_cfg.read_text(encoding="utf-8")

    # Commit .unix-primitives so it is clean
    subprocess.run(["git", "add", ".unix-primitives"], cwd=str(tmp_ws), check=True)
    subprocess.run(["git", "commit", "-m", "add config"], cwd=str(tmp_ws), check=True)

    sm.stamp_milestone(str(tmp_ws), "impl", "Impl green", "next", force=True)
    assert sm.verify_gate(str(tmp_ws)) is True


def test_verify_ignores_ticket_header(tmp_ws, sm, capsys):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Ignore ticket header test")
    # Commit empty .unix-primitives config
    repo_cfg = tmp_ws / ".unix-primitives"
    if repo_cfg.exists():
        subprocess.run(["git", "add", ".unix-primitives"], cwd=str(tmp_ws), check=True)
        subprocess.run(["git", "commit", "-m", "add config"], cwd=str(tmp_ws), check=True)

    # Inject Verify-Command into 10_ticket.md
    ticket_file = tmp_ws / ".state" / "10_ticket.md"
    content = ticket_file.read_text(encoding="utf-8")
    ticket_file.write_text("Verify-Command: false\n" + content, encoding="utf-8")

    sm.stamp_milestone(str(tmp_ws), "impl", "Impl green", "next", force=True)
    # Should pass because repo config has no Verify-Command (or true), and ticket header is ignored with warning
    res = sm.verify_gate(str(tmp_ws))
    assert res is True
    captured = capsys.readouterr()
    assert "deprecation" in captured.out.lower() or "warning" in captured.out.lower() or "deprecation" in captured.err.lower() or "warning" in captured.err.lower()


def test_verify_fails_when_config_dirty(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Dirty config test", verify_cmd="true")
    repo_cfg = tmp_ws / ".unix-primitives"
    subprocess.run(["git", "add", ".unix-primitives"], cwd=str(tmp_ws), check=True)
    subprocess.run(["git", "commit", "-m", "add config"], cwd=str(tmp_ws), check=True)

    # Modify .unix-primitives without committing
    repo_cfg.write_text("Verify-Command: false\n", encoding="utf-8")

    sm.stamp_milestone(str(tmp_ws), "impl", "Impl green", "next", force=True)
    with pytest.raises(SystemExit) as exc:
        sm.verify_gate(str(tmp_ws))
    assert exc.value.code == 1


def test_verify_allow_dirty_flag(tmp_ws, sm):
    sm.init_workspace(str(tmp_ws), "TICKET-01", "Allow dirty test", verify_cmd="true")
    repo_cfg = tmp_ws / ".unix-primitives"
    subprocess.run(["git", "add", ".unix-primitives"], cwd=str(tmp_ws), check=True)
    subprocess.run(["git", "commit", "-m", "add config"], cwd=str(tmp_ws), check=True)

    # Modify .unix-primitives without committing, but pass valid command
    repo_cfg.write_text("Verify-Command: true\n", encoding="utf-8")

    sm.stamp_milestone(str(tmp_ws), "impl", "Impl green", "next", force=True)
    assert sm.verify_gate(str(tmp_ws), allow_dirty_config=True) is True
