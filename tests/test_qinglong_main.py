import runpy
import sys
from unittest.mock import patch


def test_qinglong_main_starts_ui():
    with patch("qinglong.ui.MainPage") as mock_page:
        if "qinglong.__main__" in sys.modules:
            del sys.modules["qinglong.__main__"]
        runpy.run_module("qinglong.__main__", run_name="__main__")
        mock_page.assert_called_once()
        mock_page.return_value.start.assert_called_once()
