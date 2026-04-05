import runpy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.slow
def test_filelog_main_block_writes_log(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(REPO_ROOT / "qinglong" / "filelog.py"), run_name="__main__")
    assert (tmp_path / "app.log").exists()
