import sys
import subprocess
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "unix-primitives" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import state_manager
import unix_primitives


@pytest.fixture
def tmp_ws(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True)
    return tmp_path


@pytest.fixture
def sm():
    return state_manager


@pytest.fixture
def up():
    return unix_primitives
