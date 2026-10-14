import os
import time
import subprocess
from pathlib import Path
import pytest

REMEDY_DOC = """set -euo pipefail
git worktree add -b scratch/tx ../scratch-tx HEAD
@invariant balance >= 0
Run the test suite. Note: be brief."""


def test_classifier_canonical_doc_is_reference(up):
    findings = up.scan_text(REMEDY_DOC)
    assert findings == []
    suit = up.classify_file_suitability(REMEDY_DOC, "test.md", findings)
    assert suit["is_reference"] is True
    assert len(suit["detected_primitives"]) == 0


def test_keywords_exclude_remedy_terms(up):
    assert hasattr(up, "REMEDY_TERMS"), "REMEDY_TERMS list missing from unix_primitives.py"
    for term in up.REMEDY_TERMS:
        term_lower = term.lower()
        for p in up.PATTERNS:
            for kw in p.get("keywords", []):
                assert term_lower not in kw.lower(), f"Pattern {p['id']} keyword '{kw}' contains remedy term '{term}'"


def test_backtick_wrapped_sentence_still_flagged(up):
    text = "`If tests fail, retry until it passes.`"
    findings = up.scan_text(text)
    found_ids = [f["pattern"]["id"] for f in findings]
    assert "CIRCUIT_BREAKER" in found_ids


def test_fenced_makefile_still_stripped(up):
    text = """```makefile
ci-gate: test
	@if [ $$? -ne 0 ]; then echo retry; fi
```"""
    findings = up.scan_text(text)
    assert findings == []


def test_fenced_prose_block_scanned(up):
    text = """```
If the test suite fails, retry until it passes. This is required for verification.
```"""
    findings = up.scan_text(text)
    found_ids = [f["pattern"]["id"] for f in findings]
    assert "CIRCUIT_BREAKER" in found_ids


def test_delta_reports_backtick_gaming(tmp_path, up):
    orig = tmp_path / "orig.md"
    orig.write_text("Plain instructions without backticks.\n", encoding="utf-8")
    rewr = tmp_path / "rewr.md"
    rewr.write_text("`This is a very long line of backtick wrapped prose that spans more than forty characters.`\n", encoding="utf-8")

    report = up.format_score_delta(str(orig), str(rewr))
    assert "Backtick-wrapped prose added:" in report


def test_scan_perf_large_doc(up):
    # 5,000 lines of typical markdown text
    lines = ["# Documentation Section\n", "This is a regular explanatory sentence about architecture.\n"] * 2500
    large_doc = "".join(lines)
    start = time.perf_counter()
    findings = up.scan_text(large_doc)
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"Scanning 5,000 lines took {elapsed:.2f}s (budget: < 1.0s)"


def test_good_fixtures_are_substantive():
    fixtures_dir = Path(__file__).parent / "fixtures" / "good"
    assert fixtures_dir.exists()
    good_files = list(fixtures_dir.glob("*.md"))
    assert len(good_files) >= 17

    for f in good_files:
        lines = f.read_text(encoding="utf-8").splitlines()
        non_empty = [l for l in lines if l.strip()]
        assert len(non_empty) >= 8, f"{f.name} has only {len(non_empty)} non-empty lines (min: 8)"

        fenced_lines = 0
        in_fence = False
        for l in lines:
            if l.strip().startswith("```"):
                in_fence = not in_fence
                fenced_lines += 1
            elif in_fence:
                fenced_lines += 1

        fence_ratio = fenced_lines / max(1, len(lines))
        assert fence_ratio <= 0.30, f"{f.name} has {fence_ratio:.1%} lines in fences (max: 30%)"


def test_score_calibration_table(up):
    # Assert LOW=1, MODERATE=25, CRITICAL=60 constants
    assert up.LOW == 1
    assert up.MODERATE == 25
    assert up.CRITICAL == 60

    # 1 match in 50 lines -> between 10 and 20 (LOW band)
    f1 = [{"pattern": {"id": "CIRCUIT_BREAKER", "weight": 10}, "matches": ["retry until"]}]
    s1 = up.calculate_friction_score(f1, 50)
    assert 10 <= s1 <= 20
    assert up.LOW <= s1 < up.MODERATE

    # 3 distinct IDs in 50 lines -> >= 60 (CRITICAL band)
    f3 = [
        {"pattern": {"id": "CIRCUIT_BREAKER", "weight": 10}, "matches": ["m1"]},
        {"pattern": {"id": "MAKEFILE_DAG", "weight": 10}, "matches": ["m2"]},
        {"pattern": {"id": "SYSV_INITD", "weight": 10}, "matches": ["m3"]},
    ]
    s3 = up.calculate_friction_score(f3, 50)
    assert s3 >= up.CRITICAL


def test_cli_help_mentions_converted():
    script_path = Path(__file__).resolve().parent.parent / "skills" / "unix-primitives" / "scripts" / "unix_primitives.py"
    res = subprocess.run(["python3", str(script_path), "convert", "--help"], capture_output=True, text=True, check=True)
    assert ".converted" in res.stdout
    assert ".md" not in res.stdout or "<target>.NN.converted" in res.stdout


def test_false_positive_corpus(up):
    fp_dir = Path(__file__).parent / "fixtures" / "fp"
    if not fp_dir.exists():
        pytest.skip("FP fixtures directory not created yet")
    fp_files = list(fp_dir.glob("*.md"))
    assert len(fp_files) >= 15, f"Expected at least 15 FP files, found {len(fp_files)}"
    for f in fp_files:
        content = f.read_text(encoding="utf-8")
        findings = up.scan_text(content)
        assert findings == [], f"FP fixture {f.name} produced unexpected findings: {[item['pattern']['id'] for item in findings]}"
