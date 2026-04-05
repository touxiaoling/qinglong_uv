from unittest.mock import MagicMock, patch

import pytest

from qinglong.ui import DEFAULT_HOST, DEFAULT_PORT, PROJECT_COLUMNS, TASK_COLUMNS, error_handler, MainPage


def test_table_column_constants():
    assert PROJECT_COLUMNS and TASK_COLUMNS
    assert any(c["field"] == "name" for c in PROJECT_COLUMNS)


def test_error_handler_swallows_and_notifies():
    @error_handler
    def boom():
        raise ValueError("x")

    with patch("qinglong.ui.ui.notify") as notify:
        assert boom() is None
        notify.assert_called_once()


def test_project_and_task_selected_names():
    page = MainPage.__new__(MainPage)
    page.project_table = MagicMock()
    page.task_table = MagicMock()
    page.project_table.selected = [{"name": "p1"}]
    page.task_table.selected = [{"name": "t1"}]
    assert page.project_selected_name == "p1"
    assert page.task_selected_name == "t1"

    page.project_table.selected = []
    with pytest.raises(ValueError, match="No project selected"):
        _ = page.project_selected_name

    page.task_table.selected = []
    with pytest.raises(ValueError, match="No task selected"):
        _ = page.task_selected_name


def test_refresh_task_logs_and_stop(tmp_path, monkeypatch):
    page = MainPage.__new__(MainPage)
    page.task_logs = MagicMock()
    page.log_timer = MagicMock()
    page.current_log_task_name = "task-a"

    with patch("qinglong.ui.api.get_task_logs", return_value=["line1"]):
        page._refresh_task_logs()
    assert "line1" in page.task_logs.content

    with patch("qinglong.ui.api.get_task_logs", side_effect=RuntimeError("boom")):
        page._refresh_task_logs()
    assert "Failed" in page.task_logs.content
    page.log_timer.deactivate.assert_called()

    page._stop_log_refresh()
    page.log_timer.deactivate.assert_called()
    assert page.current_log_task_name is None


def test_save_project_config_validation(tmp_path, monkeypatch):
    page = MainPage.__new__(MainPage)
    page.project_table = MagicMock()
    page.project_table.selected = [{"name": "proj1"}]
    cfg_file = tmp_path / "app.toml"
    cfg_file.write_text("a = 1")

    page.editor = MagicMock()
    page.editor.language = "toml"
    page.editor.value = "a = 2"

    with (
        patch("qinglong.ui.api.get_project_config", return_value=cfg_file),
        patch("qinglong.ui.ui.notify") as notify,
    ):
        page.save_project_config()

    assert cfg_file.read_text() == "a = 2"
    notify.assert_called()


def test_save_project_config_invalid_toml(tmp_path):
    page = MainPage.__new__(MainPage)
    page.project_table = MagicMock()
    page.project_table.selected = [{"name": "proj1"}]
    cfg_file = tmp_path / "a.toml"
    cfg_file.touch()
    page.editor = MagicMock()
    page.editor.language = "toml"
    page.editor.value = "not valid toml [[["

    with (
        patch("qinglong.ui.api.get_project_config", return_value=cfg_file),
        patch("qinglong.ui.ui.notify") as notify,
    ):
        page.save_project_config()

    notify.assert_called()
    assert "TOML" in str(notify.call_args)


def test_save_project_config_unsupported_language(tmp_path):
    page = MainPage.__new__(MainPage)
    page.project_table = MagicMock()
    page.project_table.selected = [{"name": "proj1"}]
    cfg_file = tmp_path / "x.txt"
    cfg_file.touch()
    page.editor = MagicMock()
    page.editor.language = "json"
    page.editor.value = "{}"

    with (
        patch("qinglong.ui.api.get_project_config", return_value=cfg_file),
        patch("qinglong.ui.ui.notify") as notify,
    ):
        page.save_project_config()

    assert "Unsupported" in str(notify.call_args)


def test_mainpage_start_runs_ui():
    page = MainPage.__new__(MainPage)
    page.update_project_table = MagicMock()
    page.update_task_table = MagicMock()

    with patch("qinglong.ui.ui.run") as run:
        page.start(host="127.0.0.1", port=9000, debug=True)

    run.assert_called_once()
    assert run.call_args.kwargs["host"] == "127.0.0.1"
    assert run.call_args.kwargs["port"] == 9000
    assert DEFAULT_HOST == "0.0.0.0"
    assert DEFAULT_PORT == 80
