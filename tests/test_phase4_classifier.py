import os
from pathlib import Path
import pytest


def test_score_monotonic_in_matches(up):
    # 1 match vs 2 matches on same line count
    findings_1 = [{"pattern": {"id": "SYSV_INITD", "weight": 10}, "matches": ["match1"]}]
    findings_2 = [{"pattern": {"id": "SYSV_INITD", "weight": 10}, "matches": ["match1", "match2"]}]

    score_1 = up.calculate_friction_score(findings_1, 50)
    score_2 = up.calculate_friction_score(findings_2, 50)
    assert score_2 > score_1


def test_score_density_normalized(up):
    # Same 3 matches in a 20-line file vs a 500-line file
    findings = [{"pattern": {"id": "MAKEFILE_DAG", "weight": 10}, "matches": ["m1", "m2", "m3"]}]
    score_short = up.calculate_friction_score(findings, 20)
    score_long = up.calculate_friction_score(findings, 500)

    assert score_short > score_long
    assert score_long < 30


def test_score_zero_when_no_findings(up):
    assert up.calculate_friction_score([], 100) == 0


def test_reference_doc_classified_as_reference(up):
    tech_stack_doc = """# Backend Architecture
This service uses Python 3.11, FastAPI, and PostgreSQL.
Dependencies are managed using pip and uv.

```bash
npm install
pytest
```
"""
    suit = up.classify_file_suitability(tech_stack_doc, "README.md", [])
    assert suit["is_reference"] is True
    assert len(suit["detected_primitives"]) == 0



def test_audit_prompt_lists_all_17_ids(up):
    prompt = up.generate_subagent_prompt("README.md")
    for p in up.PATTERNS:
        assert p["id"] in prompt, f"Primitive ID {p['id']} missing from generated audit prompt"


def test_convert_path_not_md(up):
    out = up.get_next_increment_path("CLAUDE.md")
    assert not out.endswith(".md")
    assert out.endswith(".01.converted")


def test_convert_path_dotfile(up):
    out = up.get_next_increment_path(".cursorrules")
    assert not out.endswith(".md")
    assert out.endswith(".01.converted")
    assert ".cursorrules.01.converted" in out


def test_convert_increments(tmp_path, up):
    target = tmp_path / "CLAUDE.md"
    target.write_text("# Claude rules\n", encoding="utf-8")

    out1 = up.get_next_increment_path(str(target))
    assert out1.endswith(".01.converted")
    Path(out1).write_text("v1", encoding="utf-8")

    out2 = up.get_next_increment_path(str(target))
    assert out2.endswith(".02.converted")
