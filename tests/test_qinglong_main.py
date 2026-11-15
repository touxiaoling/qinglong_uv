import os
import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


def test_qinglong_main_starts_fastapi():
    with patch("uvicorn.run") as run:
        if "qinglong.__main__" in sys.modules:
            del sys.modules["qinglong.__main__"]
        runpy.run_module("qinglong.__main__", run_name="__main__")
        run.assert_called_once_with("qinglong.web:app", host="0.0.0.0", port=80, workers=1)


def test_docker_entrypoint_runs_maintenance_before_launch(tmp_path):
    uv = tmp_path / "uv"
    uv.write_text('#!/bin/sh\nprintf "%s|%s|%s\\n" "$*" "${UV_PYTHON:-}" "${UV_MANAGED_PYTHON:-}"\n[ "$*" != "self update" ]\n')
    uv.chmod(0o755)
    entrypoint = Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"
    result = subprocess.run(
        ["sh", str(entrypoint)],
        env={**os.environ, "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}", "UV_PYTHON": "3.15", "UV_MANAGED_PYTHON": ""},
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.stdout.splitlines() == [
        "self update|3.15|",
        "python upgrade||",
        "cache prune --force|3.15|",
        "run --locked --no-dev -m qinglong|3.15|1",
    ]
    assert "Could not update uv" in result.stderr
