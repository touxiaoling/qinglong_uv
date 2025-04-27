from typing import Optional, Callable
import logging

from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent, QPixmap, Qt, QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QTableView
from .ui_main import Ui_MainWindow
from .ui_pull_project import Ui_pullProject
from .ui_set_task import Ui_setTask
from .api import QingLongApi
from qinglong.data_struct import TaskInfo, ProjectInfo

_logger = logging.getLogger(__name__)


class PullProjectWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_pullProject()
        self.ui.setupUi(self)
        self.ui.okButton.clicked.connect(self.on_click_ok_button)
        self.ui.cancelButton.clicked.connect(self.on_click_cancel_button)
        self.project_info = None

    def on_click_ok_button(self):
        self.project_info = self.get_project_info()
        self.accept()

    def on_click_cancel_button(self):
        self.reject()

    def get_project_info(self):
        name = self.ui.nameEdit.text()
        url = self.ui.urlEdit.text()
        one_file = self.ui.oneFileCheckBox.isChecked()

        if not name:
            name = url.split("/")[-1]

        if not url:
            QMessageBox.warning(self, "Error", "URL cannot be empty")
            return

        return name, url, one_file


class SetTaskWindow(QDialog):
    def __init__(self, project_name: str):
        super().__init__()
        self.ui = Ui_setTask()
        self.ui.setupUi(self)

        self.project_name = project_name
        self.task_info = None

        self.ui.okButton.clicked.connect(self.on_click_ok_button)
        self.ui.cancelButton.clicked.connect(self.on_click_cancel_button)

    def on_click_ok_button(self):
        task_info = self.get_task_info()
        self.task_info = task_info
        self.accept()

    def on_click_cancel_button(self):
        self.reject()

    def get_task_info(self):
        name = self.ui.nameEdit.text()
        cron = self.ui.cronEdit.text()
        cmd = self.ui.cmdEdit.text()

        if not name:
            name = self.project_name

        return name, cron, cmd


class CustomStandardItemModel(QStandardItemModel):
    def __init__(self, rows, columns, custom_data):
        super().__init__(rows, columns)
        self._custom_data = custom_data

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return super().data(index, role)
        return super().data(index, role)


class MainWindow(QMainWindow):
    def __init__(self,ip):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.api = QingLongApi(ip, "your_token_here")

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["name", "path", "upgrade_at", "created_at", "url"])
        self.ui.projectView.setModel(model)
        self.ui.projectView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.ui.projectView.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.ui.projectView.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["name", "project_name", "status", "cron", "cmd", "upgrade_at", "created_at"])
        self.ui.taskView.setModel(model)
        self.ui.taskView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.ui.taskView.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.ui.taskView.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        self.ui.pullButton.clicked.connect(self.on_click_pull_button)
        self.ui.upgradeButton.clicked.connect(self.on_click_upgrade_button)
        self.ui.removeButton.clicked.connect(self.on_click_remove_button)

        self.ui.setButton.clicked.connect(self.on_click_set_button)
        self.ui.removeButton_2.clicked.connect(self.on_click_remove_task_button)
        self.ui.startButton.clicked.connect(self.on_click_start_task_button)
        self.ui.pauseButton.clicked.connect(self.on_click_pause_task_button)

        self.set_project_view()
        self.set_task_view()

    def set_project_view(self):
        project_infos: dict = self.api.get_project_list()
        model: QStandardItemModel = self.ui.projectView.model()
        model.setRowCount(len(project_infos))
        for row, project in enumerate(project_infos.values()):
            model.setItem(row, 0, QStandardItem(project["name"]))
            model.setItem(row, 1, QStandardItem(project["project_path"]))
            model.setItem(row, 2, QStandardItem(project["upgrade_at"]))
            model.setItem(row, 3, QStandardItem(project["created_at"]))
            model.setItem(row, 4, QStandardItem(project["url"]))

    def set_task_view(self):
        task_infos: dict = self.api.get_task_list()
        model: QStandardItemModel = self.ui.taskView.model()
        model.setRowCount(len(task_infos))
        for row, task in enumerate(task_infos.values()):
            model.setItem(row, 0, QStandardItem(task["name"]))
            model.setItem(row, 1, QStandardItem(task["project_name"]))
            model.setItem(row, 2, QStandardItem(task["status"]))
            model.setItem(row, 3, QStandardItem(task["cron"]))
            model.setItem(row, 4, QStandardItem(task["command"]))
            model.setItem(row, 5, QStandardItem(task["upgrade_at"]))
            model.setItem(row, 6, QStandardItem(task["created_at"]))

    def get_view_select_name(self, qview: QTableView):
        selected_index = qview.selectedIndexes()
        if not selected_index:
            return None
        item_index = selected_index[0].row()
        view_model = self.ui.projectView.model()
        name = view_model.item(item_index, 0).text()
        _logger.debug(f"get_view_select_name: {name}")
        return name

    def on_click_pull_button(self):
        pull_project_window = PullProjectWindow()
        result = pull_project_window.exec()
        if QDialog.DialogCode.Accepted != result:
            return
        project_name, url, one_file = pull_project_window.project_info
        self.api.pull_project(project_name, url, one_file)
        self.set_project_view()

    def on_click_remove_button(self):
        project_name = self.get_view_select_name(self.ui.projectView)
        if not project_name:
            QMessageBox.warning(self, "Error", "Please select a project")
            return
        self.api.remove_project(project_name)
        self.set_project_view()

    def on_click_upgrade_button(self):
        project_name = self.get_view_select_name(self.ui.projectView)
        if not project_name:
            QMessageBox.warning(self, "Error", "Please select a project")
            return
        self.api.upgrade_project(project_name)
        self.set_project_view()

    def on_click_set_button(self):
        project_name = self.get_view_select_name(self.ui.projectView)
        if not project_name:
            QMessageBox.warning(self, "Error", "Please select a project")
            return

        set_task_windows = SetTaskWindow(project_name=project_name)
        result = set_task_windows.exec()
        if QDialog.DialogCode.Accepted != result:
            return
        name, cron, cmd = set_task_windows.task_info
        self.api.set_task(name, project_name, cron, cmd)
        self.set_task_view()

    def on_click_remove_task_button(self):
        task_name = self.get_view_select_name(self.ui.taskView)
        if not task_name:
            QMessageBox.warning(self, "Error", "Please select a task")
            return
        self.api.remove_task(task_name)
        self.set_task_view()

    def on_click_start_task_button(self):
        task_name = self.get_view_select_name(self.ui.taskView)
        if not task_name:
            QMessageBox.warning(self, "Error", "Please select a task")
            return
        self.api.start_task(task_name)
        self.set_task_view()

    def on_click_pause_task_button(self):
        task_name = self.get_view_select_name(self.ui.taskView)
        if not task_name:
            QMessageBox.warning(self, "Error", "Please select a task")
            return
        self.api.pause_task(task_name)
        self.set_task_view()


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    _logger.debug("Starting Qinglong UI")
    ip = sys.argv[1] if len(sys.argv) > 1 else "localhost:8090"
    app = QApplication([])
    main_window = MainWindow(ip)
    main_window.show()
    app.exec()
