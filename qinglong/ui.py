import logging
import tomllib
from functools import wraps

from nicegui import ui
import yaml

from . import api

_logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 80
DIALOG_WIDTH = "min-w-[50%] min-h-[100%]"

# 表格列定义
PROJECT_COLUMNS = [
    {"name": "name", "label": "Name", "field": "name", "required": True, "align": "left"},
    {"name": "path", "label": "Path", "field": "project_path", "sortable": True},
    {"name": "upgrade_at", "label": "Upgrade At", "field": "upgrade_at", "sortable": True},
    {"name": "created_at", "label": "Created At", "field": "created_at", "sortable": True},
    {"name": "url", "label": "Url", "field": "url", "sortable": True},
]

TASK_COLUMNS = [
    {"name": "name", "label": "Name", "field": "name", "required": True, "align": "left"},
    {"name": "project_name", "label": "Project Name", "field": "project_name", "sortable": True},
    {"name": "status", "label": "Status", "field": "status", "sortable": True},
    {"name": "cron", "label": "Cron", "field": "cron", "sortable": True},
    {"name": "cmd", "label": "Cmd", "field": "command", "sortable": True},
    {"name": "upgrade_at", "label": "Upgrade At", "field": "upgrade_at", "sortable": True},
    {"name": "created_at", "label": "Created At", "field": "created_at", "sortable": True},
]


def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _logger.error(f"{func.__name__} failed: {e}")
            ui.notify(f"Operation failed: {e}", type="negative")

    return wrapper


class MainPage:
    def __init__(self):
        try:
            api.init_task()
            self._init_dialogs()
            self._init_ui()
        except Exception as e:
            _logger.error(f"初始化失败: {e}")
            raise

    def _init_dialogs(self) -> None:
        """初始化所有对话框"""
        with ui.dialog() as self.dialog, ui.card().style("max-width: none"):
            # 任务日志
            self.task_logs = ui.markdown()

        with ui.dialog() as self.dialog2, ui.card():
            # 删除项目确认
            ui.label("Are you sure you want to remove this project?")
            with ui.row():
                ui.button("OK", on_click=self.remove_project)
                ui.button("CANCEL", on_click=self.dialog2.close)

        with ui.dialog() as self.dialog_config, ui.card().style("max-width: none").classes(DIALOG_WIDTH):
            # 项目配置
            self.editor_label = ui.label("Project Config")
            self.editor = ui.codemirror("", language="toml", theme="vscodeDark").classes("flex-grow")
            with ui.button_group():
                ui.button("Save", on_click=self.save_project_config)
                ui.button("Cancel", on_click=self.dialog_config.close)

    def _init_ui(self) -> None:
        """初始化主界面"""
        ui.label("Project")
        with ui.row():
            self.input_project_name = ui.input(label="Name", placeholder="Project Name")
            self.input_project_url = ui.input(label="URL", placeholder="Project URL")
        with ui.button_group():
            ui.button("Clone", on_click=self.clone_project)
            ui.button("Pull", on_click=self.pull_project)
            ui.button("Remove", on_click=self.dialog2.open)
            ui.button("Config", on_click=self.start_config_project)
        self.project_table = ui.table(columns=PROJECT_COLUMNS, rows=[], row_key="name", selection="single")

        ui.label("Task")
        with ui.row():
            self.input_task_name = ui.input(label="Name", placeholder="Task Name")
            self.input_task_cron = ui.input(label="Cron", placeholder="Cron Expression")
            self.input_task_cmd = ui.input(label="Command", placeholder="Command")
        with ui.button_group():
            ui.button("Set", on_click=self.set_task)
            ui.button("Remove", on_click=self.remove_task)
            ui.button("Sync", on_click=self.sync_task)
        self.task_table = ui.table(columns=TASK_COLUMNS, rows=[], row_key="name", selection="single")
        with ui.button_group():
            ui.button("Start", on_click=self.start_task)
            ui.button("Pause", on_click=self.pause_task)
            ui.button("Run", on_click=self.run_task)
            ui.button("Logs", on_click=self.show_task_logs)

    @property
    def project_selected_name(self) -> str:
        """获取选中的项目名称"""
        if not self.project_table.selected:
            raise ValueError("No project selected")
        return self.project_table.selected[0]["name"]

    @property
    def task_selected_name(self) -> str:
        """获取选中的任务名称"""
        if not self.task_table.selected:
            raise ValueError("No task selected")
        return self.task_table.selected[0]["name"]

    @error_handler
    def update_project_table(self) -> None:
        """更新项目表格"""
        projects = api.list_projects()
        self.project_table.update_rows(projects)

    @error_handler
    def update_task_table(self) -> None:
        """更新任务表格"""
        tasks = api.list_tasks()
        self.task_table.update_rows(tasks)

    @error_handler
    def clone_project(self) -> None:
        """克隆项目"""
        name = self.input_project_name.value
        url = self.input_project_url.value
        if not url:
            ui.notify("Please fill in project URL", type="warning")
            return
        ui.notify(f"Cloning {name}:{url}...")
        api.clone_project(url, name)
        self.update_project_table()

    @error_handler
    def pull_project(self) -> None:
        """拉取项目更新"""
        ui.notify(f"Pulling {self.project_selected_name}...")
        api.pull_project(self.project_selected_name)
        self.update_project_table()

    @error_handler
    def remove_project(self) -> None:
        """删除项目"""
        ui.notify(f"Removing {self.project_selected_name}...")
        api.remove_project(self.project_selected_name)
        self.update_project_table()
        self.dialog2.close()

    @error_handler
    def start_config_project(self) -> None:
        """开始配置项目"""
        config_file = api.get_project_config(self.project_selected_name)
        if config_file is None:
            ui.notify("Config file not found", type="warning")
            return

        self.editor.language = config_file.suffix[1:]
        self.editor.value = config_file.read_text()
        self.editor_label.set_text(f"Project Config: {config_file.name}")
        self.dialog_config.open()

    @error_handler
    def save_project_config(self) -> None:
        """保存项目配置"""
        config_file = api.get_project_config(self.project_selected_name)
        if config_file is None:
            ui.notify("Config file not found", type="warning")
            return

        language = self.editor.language
        content = self.editor.value

        # 验证配置文件格式
        if language == "toml":
            try:
                tomllib.loads(content)
            except Exception as e:
                ui.notify(f"Invalid TOML format: {e}", type="negative")
                return
        elif language == "yaml":
            try:
                yaml.safe_load(content)
            except Exception as e:
                ui.notify(f"Invalid YAML format: {e}", type="negative")
                return
        else:
            ui.notify(f"Unsupported language: {language}", type="negative")
            return

        config_file.write_text(content)
        self.dialog_config.close()
        ui.notify("Config saved successfully", type="positive")

    @error_handler
    def set_task(self) -> None:
        """设置任务"""
        name = self.input_task_name.value
        project_name = self.project_selected_name
        cron = self.input_task_cron.value
        cmd = self.input_task_cmd.value

        if not all([name, project_name, cron, cmd]):
            ui.notify("Please fill in all required fields", type="warning")
            return

        ui.notify(f"Setting {name}...")
        api.set_task(name, project_name, cron, cmd)
        self.update_task_table()

    @error_handler
    def remove_task(self) -> None:
        """删除任务"""
        ui.notify(f"Removing {self.task_selected_name}...")
        api.remove_task(self.task_selected_name)
        self.update_task_table()

    @error_handler
    def start_task(self) -> None:
        """启动任务"""
        ui.notify(f"Starting {self.task_selected_name}...")
        api.start_task(self.task_selected_name)
        self.update_task_table()

    @error_handler
    def pause_task(self) -> None:
        """暂停任务"""
        ui.notify(f"Pausing {self.task_selected_name}...")
        api.pause_task(self.task_selected_name)
        self.update_task_table()

    @error_handler
    def run_task(self) -> None:
        """运行任务"""
        ui.notify(f"Running {self.task_selected_name}...")
        api.run_task(self.task_selected_name)
        self.update_task_table()

    @error_handler
    def show_task_logs(self) -> None:
        """显示任务日志"""
        task_name = self.task_selected_name
        task_logs = "\n".join(api.get_task_logs(task_name))
        self.task_logs.content = f"```\n{task_logs}\n```"
        self.dialog.open()

    @error_handler
    def sync_task(self) -> None:
        """同步任务"""
        ui.notify("Syncing tasks...")
        api.sync_task()
        self.update_task_table()

    @error_handler
    def start(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, debug: bool = False) -> None:
        """启动应用"""
        self.update_project_table()
        self.update_task_table()
        ui.run(host=host, port=port, title="Qinglong", dark=None, reload=debug, show=debug, uvicorn_reload_dirs="qinglong")
