import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_readme_has_evidence_section():
    """Verify README.md contains an explicit Evidence & Empirical Validation section with all required details."""
    readme_path = REPO_ROOT / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text(encoding="utf-8")

    assert "## Evidence & Empirical Validation" in content or "## Evidence" in content
    for term in ["1,680", "Gemini", "flash-lite", "slabb", "bespoke", "Level 2", "Fisher", "Wilson"]:
        assert term in content, f"README.md missing required evidence term: {term}"
    assert "## The Core Problem: The Zero-Frequency Interpreter Trap" not in content


def test_enforcement_column_present():
    """Verify 17 primitives tables contain the Enforcement column and POSIX Signals is Prompt-only."""
    readme_path = REPO_ROOT / "README.md"
    primitives_ref = REPO_ROOT / "skills" / "unix-primitives" / "references" / "primitives.md"

    for file_path in [readme_path, primitives_ref]:
        content = file_path.read_text(encoding="utf-8")
        assert "Enforcement" in content, f"{file_path.name} missing 'Enforcement' column header"
        assert "Host" in content, f"{file_path.name} missing 'Host' enforcement level"
        assert "Prompt-only" in content, f"{file_path.name} missing 'Prompt-only' enforcement level"

        for line in content.splitlines():
            if "POSIX Signals" in line and "|" in line:
                assert "Prompt-only" in line, f"{file_path.name}: POSIX Signals row must have 'Prompt-only' enforcement, got: {line}"


def test_skill_md_size_budget():
    """Verify SKILL.md remains strictly within the 6144-byte context budget."""
    skill_md = REPO_ROOT / "skills" / "unix-primitives" / "SKILL.md"
    assert skill_md.exists()
    size = skill_md.stat().st_size
    assert size <= 6144, f"SKILL.md exceeded 6144-byte budget ({size} bytes > 6144 bytes)"


def test_readme_findings_only_from_example_table(up):
    readme_path = REPO_ROOT / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")

    lines = readme_text.splitlines()
    table_start_idx = None
    table_end_idx = None
    for i, line in enumerate(lines):
        if "## The 17 Canonical Primitives" in line:
            table_start_idx = i
            break
    assert table_start_idx is not None, "Table heading not found"
    for i in range(table_start_idx + 1, len(lines)):
        if lines[i].startswith("---") or (lines[i].startswith("## ") and "## The 17" not in lines[i]):
            table_end_idx = i
            break
    assert table_end_idx is not None, "Table end delimiter not found"

    table_start_char = len("\n".join(lines[:table_start_idx])) + 1
    table_end_char = len("\n".join(lines[:table_end_idx]))

    findings = up.scan_text(readme_text)
    finding_ids = {f["pattern"]["id"] for f in findings}

    assert "RING_BUFFER" not in finding_ids
    assert finding_ids == {"DESIGN_BY_CONTRACT", "LKML_PATCH_SERIES", "FILE_LOCKING"}

    for f in findings:
        for m in f["matches"]:
            idx = readme_text.find(m)
            assert idx != -1
            assert table_start_char <= idx <= table_end_char, f"Match '{m}' for {f['pattern']['id']} found outside 17 primitives table"



def test_documented_cli_commands_parse(tmp_ws):
    """Every documented `python3 .../state_manager.py ...` line in skills/ must be accepted by argparse."""
    import re
    import shlex
    import subprocess
    import sys

    script = REPO_ROOT / "skills" / "unix-primitives" / "scripts" / "state_manager.py"
    line_re = re.compile(r"python3\s+(?:\S*state_manager\.py|\"<STATE_MANAGER>\")\s+(.*)$")
    commands = []
    for md in sorted((REPO_ROOT / "skills").rglob("*.md")):
        for line in md.read_text(encoding="utf-8").splitlines():
            m = line_re.search(line)
            if not m:
                continue
            args = m.group(1).split("<<")[0]
            args = args.replace("$(REPO_ROOT)", str(tmp_ws)).replace("[", " ").replace("]", " ")
            args = re.sub(r"<([^<>|]+)(?:\|[^<>]+)?>", r"\1", args)  # <a|b> -> a, <x> -> x
            args = re.sub(r"(\S+?)\|\S+", r"\1", args)              # a|b -> a
            commands.append((md.relative_to(REPO_ROOT), shlex.split(args)))

    assert len(commands) >= 8, f"expected documented CLI lines, found {len(commands)}"
    for src, argv in commands:
        res = subprocess.run([sys.executable, str(script), *argv], cwd=str(tmp_ws),
                             input="", capture_output=True, text=True)
        assert res.returncode != 2, f"{src}: argparse rejected {argv}: {res.stderr.strip()}"
