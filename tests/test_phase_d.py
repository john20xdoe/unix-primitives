import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_readme_has_evidence_section():
    """Verify README.md contains an explicit Evidence & Empirical Validation section."""
    readme_path = REPO_ROOT / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text(encoding="utf-8")

    assert "## Evidence & Empirical Validation" in content or "## Evidence" in content
    # Verify discussion of the 4 arms
    for arm in ["prose", "bespoke", "canonical", "host"]:
        assert arm in content
    # Verify statistical rigor terms
    assert "Fisher" in content
    assert "Wilson" in content
    # Verify Level 1 vs Level 2 distinction
    assert "Level 1" in content or "Level 2" in content


def test_enforcement_column_present():
    """Verify 17 primitives tables contain the Enforcement column (Host vs Prompt-only)."""
    readme_path = REPO_ROOT / "README.md"
    primitives_ref = REPO_ROOT / "skills" / "unix-primitives" / "references" / "primitives.md"

    for file_path in [readme_path, primitives_ref]:
        content = file_path.read_text(encoding="utf-8")
        assert "Enforcement" in content, f"{file_path.name} missing 'Enforcement' column header"
        assert "Host" in content, f"{file_path.name} missing 'Host' enforcement level"
        assert "Prompt-only" in content, f"{file_path.name} missing 'Prompt-only' enforcement level"


def test_skill_md_size_budget():
    """Verify SKILL.md remains strictly within the 6144-byte context budget."""
    skill_md = REPO_ROOT / "skills" / "unix-primitives" / "SKILL.md"
    assert skill_md.exists()
    size = skill_md.stat().st_size
    assert size <= 6144, f"SKILL.md exceeded 6144-byte budget ({size} bytes > 6144 bytes)"
