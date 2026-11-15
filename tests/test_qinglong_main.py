import runpy
import sys
from unittest.mock import patch


def test_qinglong_main_starts_fastapi():
    with patch("uvicorn.run") as run:
        if "qinglong.__main__" in sys.modules:
            del sys.modules["qinglong.__main__"]
        runpy.run_module("qinglong.__main__", run_name="__main__")
        run.assert_called_once_with("qinglong.web:app", host="0.0.0.0", port=80, workers=1)
