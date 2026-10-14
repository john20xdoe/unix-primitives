import re
from pathlib import Path
import pytest

ROSETTA_PATH = Path(__file__).resolve().parent.parent / "skills" / "unix-primitives" / "references" / "rosetta_stone.md"


def get_rosetta_snippets():
    if not ROSETTA_PATH.exists():
        return []
    content = ROSETTA_PATH.read_text(encoding="utf-8")
    blocks = re.findall(r"```(?:\w+)?\n([\s\S]*?)```", content)
    return [b.strip() for b in blocks if b.strip()]


def test_canonical_snippets_score_zero(up):
    # Test all PATTERNS snippets
    for p in up.PATTERNS:
        snippet = p.get("snippet", "")
        if snippet:
            findings = up.scan_text(snippet)
            found_ids = [f["pattern"]["id"] for f in findings]
            assert not found_ids, f"Pattern snippet for {p['id']} triggered: {found_ids}"

    # Test all rosetta stone snippets
    rosetta_snippets = get_rosetta_snippets()
    assert len(rosetta_snippets) > 0, "No rosetta snippets found"
    for i, snip in enumerate(rosetta_snippets):
        findings = up.scan_text(snip)
        found_ids = [f["pattern"]["id"] for f in findings]
        assert not found_ids, f"Rosetta stone snippet #{i} triggered: {found_ids} for content:\n{snip}"


def test_canonical_remedies_score_zero(up):
    text = """set -euo pipefail
git worktree add -b scratch/tx ../scratch-tx HEAD
@invariant balance >= 0"""
    findings = up.scan_text(text)
    assert findings == []


def test_lkml_no_cross_line_match(up):
    text = "Run the test suite. Note: be brief."
    findings = up.scan_text(text)
    found_ids = [f["pattern"]["id"] for f in findings]
    assert "LKML_PATCH_SERIES" not in found_ids


def test_plain_numbered_list_not_flagged(up):
    text = """1. Clone repository
2. Install dependencies with pip
3. Start the application"""
    findings = up.scan_text(text)
    found_ids = [f["pattern"]["id"] for f in findings]
    assert "MAKEFILE_DAG" not in found_ids


def test_goto_list_flagged(up):
    text = """1. Run tests
2. If fail, go back to step 1"""
    findings = up.scan_text(text)
    found_ids = [f["pattern"]["id"] for f in findings]
    assert "MAKEFILE_DAG" in found_ids


def test_bad_fixtures_trigger_expected_id(up):
    fixtures_dir = Path(__file__).parent / "fixtures" / "bad"
    if not fixtures_dir.exists():
        pytest.skip("Fixtures not created yet")
    bad_files = list(fixtures_dir.glob("*.md"))
    assert len(bad_files) >= 17
    for f in bad_files:
        expected_id = f.stem
        content = f.read_text(encoding="utf-8")
        findings = up.scan_text(content)
        found_ids = [item["pattern"]["id"] for item in findings]
        assert expected_id in found_ids, f"File {f.name} did not trigger {expected_id}. Found: {found_ids}"


def test_good_fixtures_clean(up):
    fixtures_dir = Path(__file__).parent / "fixtures" / "good"
    if not fixtures_dir.exists():
        pytest.skip("Fixtures not created yet")
    good_files = list(fixtures_dir.glob("*.md"))
    assert len(good_files) >= 17
    for f in good_files:
        content = f.read_text(encoding="utf-8")
        findings = up.scan_text(content)
        found_ids = [item["pattern"]["id"] for item in findings]
        assert not found_ids, f"Good file {f.name} triggered unexpected findings: {found_ids}"
