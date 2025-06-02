import logging
from nicegui import ui

from .config import settings as cfg
from . import api


_logger = logging.getLogger(__name__)
# "name", "path", "upgrade_at", "created_at", "url"
project_columns = [
    {"name": "name", "label": "Name", "field": "name", "required": True, "align": "left"},
    {"name": "path", "label": "Path", "field": "project_path", "sortable": True},
    {"name": "upgrade_at", "label": "Upgrade At", "field": "upgrade_at", "sortable": True},
    {"name": "created_at", "label": "Created At", "field": "created_at", "sortable": True},
    {"name": "url", "label": "Url", "field": "url", "sortable": True},
]

# "name", "project_name", "status", "cron", "cmd", "upgrade_at", "created_at"
task_columns = [
    {"name": "name", "label": "Name", "field": "name", "required": True, "align": "left"},
    {"name": "project_name", "label": "Project Name", "field": "project_name", "sortable": True},
    {"name": "status", "label": "Status", "field": "status", "sortable": True},
    {"name": "cron", "label": "Cron", "field": "cron", "sortable": True},
    {"name": "cmd", "label": "Cmd", "field": "command", "sortable": True},
    {"name": "upgrade_at", "label": "Upgrade At", "field": "upgrade_at", "sortable": True},
    {"name": "created_at", "label": "Created At", "field": "created_at", "sortable": True},
]


class MainPage:
    def __init__(self):
        api.init_task()

        with ui.dialog() as self.dialog2, ui.card():
            ui.label("Are you sure you want to remove this project?")
            with ui.row():
                ui.button("OK", on_click=self.remove_project)
                ui.button("CANCEL", on_click=self.dialog2.close)

        ui.label("Project")
        with ui.grid(columns=3):
            self.input_project_name = ui.input(label="name", placeholder="项目名称")
            self.input_project_url = ui.input(label="url", placeholder="项目路径")
        with ui.button_group():
            ui.button("pull", on_click=self.pull_project)
            ui.button("upgrade", on_click=self.upgrade_project)
            ui.button("remove", on_click=self.dialog2.open)
        self.project_table = ui.table(columns=project_columns, rows=[], row_key="name", selection="single")

        ui.label("Task")
        with ui.grid(columns=3):
            self.input_task_name = ui.input(label="name", placeholder="任务名称")
            self.input_task_cron = ui.input(label="cron", placeholder="cron")
            self.input_task_cmd = ui.input(label="cmd", placeholder="cmd")
        with ui.button_group():
            ui.button("set", on_click=self.set_task)
            ui.button("remove", on_click=self.remove_task)
            ui.button("sync", on_click=self.sync_task)
        self.task_table = ui.table(columns=task_columns, rows=[], row_key="name", selection="single")
        with ui.button_group():
            ui.button("start", on_click=self.start_task)
            ui.button("pause", on_click=self.pause_task)
            ui.button("run", on_click=self.run_task)
            ui.button("logs", on_click=self.show_task_logs)

        with ui.dialog() as self.dialog, ui.card().style("max-width: none").classes("max-w-0.9"):
            self.task_logs = ui.markdown()

    @property
    def project_selected_name(self):
        return self.project_table.selected[0]["name"]

    @property
    def task_selected_name(self):
        return self.task_table.selected[0]["name"]

    def update_project_table(self):
        projects = api.list_projects()
        self.project_table.update_rows(projects)

    def update_task_table(self):
        tasks = api.list_tasks()
        self.task_table.update_rows(tasks)

    def pull_project(self):
        name = self.input_project_name.value
        url = self.input_project_url.value
        ui.notify(f"pulling {name}:{url}...")
        api.pull_project(url, name)
        self.update_project_table()

    def upgrade_project(self):
        ui.notify(f"upgrading {self.project_selected_name}...")
        api.upgrade_project(self.project_selected_name)
        self.update_project_table()

    def remove_project(self):
        ui.notify(f"removing {self.project_selected_name}...")
        api.remove_project(self.project_selected_name)
        self.update_project_table()
        self.dialog2.close()

    def set_task(self):
        name = self.input_task_name.value
        project_name = self.project_selected_name
        cron = self.input_task_cron.value
        cmd = self.input_task_cmd.value
        ui.notify(f"setting {name}...")
        api.set_task(name, project_name, cron, cmd)
        self.update_task_table()

    def remove_task(self):
        ui.notify(f"removing {self.task_selected_name}...")
        api.remove_task(self.task_selected_name)
        self.update_task_table()

    def start_task(self):
        ui.notify(f"starting {self.task_selected_name}...")
        api.start_task(self.task_selected_name)
        self.update_task_table()

    def pause_task(self):
        ui.notify(f"pausing {self.task_selected_name}...")
        api.pause_task(self.task_selected_name)
        self.update_task_table()

    def run_task(self):
        ui.notify(f"running {self.task_selected_name}...")
        api.run_task(self.task_selected_name)
        self.update_task_table()

    def show_task_logs(self):
        task_name = self.task_selected_name
        task_logs = api.get_task_logs(task_name)
        task_logs = "\n".join(task_logs)
        self.task_logs.content = f"```\n{task_logs}\n```"
        self.dialog.open()

    def sync_task(self):
        ui.notify("syncing tasks...")
        api.sync_task()
        self.update_task_table()

    def start(self, host="0.0.0.0", port=80, debug=False):
        self.update_project_table()
        self.update_task_table()
        ui.run(host=host, port=port, title="Qinglong", dark=None, reload=debug, show=debug, uvicorn_reload_dirs="qinglong")
