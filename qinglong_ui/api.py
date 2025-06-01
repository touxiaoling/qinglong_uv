import logging

import httpx

_logger = logging.getLogger(__name__)


class QingLongApi:
    def __init__(self, host: str, token: str = ""):
        self.host = host
        self.token = token
        self.client = httpx.Client(http2=True, timeout=10)

    def _get(self, path: str, params: dict = None):
        url = f"{self.host}/api/{path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get(url, headers=headers, params=params)
        response.raise_for_status()
        response = response.json()
        _logger.debug(f"GET {url} {params} -> {response}")
        return response

    def _post(self, path: str, data: dict = None):
        url = f"{self.host}/api/{path}"
        # headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.post(url, json=data)
        if response.status_code != 200:
            _logger.error(f"POST {url} {data} -> {response.status_code} {response.text}")
            response.raise_for_status()
        response = response.json()
        _logger.debug(f"POST {url} {data} -> {response}")
        return response

    def get_project_list(self):
        return self._get("project_list")

    def get_task_list(self):
        return self._get("task_list")

    def upload_script(self, name: str, file: bytes):
        data = {"name": name, "file": file}
        self._post("upload_script", data=data)

    def pull_project(self, name: str, url: str, one_file: bool = False):
        data = {"name": name, "url": url, "one_file": one_file}
        _logger.debug(f"Pulling project: {data}")
        self._post("pull_project", data=data)

    def upgrade_project(self, project_name: str):
        self._post("upgrade_project", data={"project_name": project_name})

    def remove_project(self, project_name: str):
        self._post("remove_project", data={"project_name": project_name})

    def set_task(self, name: str, project_name: str, cron: str, command: str):
        data = {"name": name, "project_name": project_name, "cron": cron, "command": command}
        self._post("set_task", data=data)

    def remove_task(self, task_name: str):
        self._post("remove_task", data={"task_name": task_name})

    def start_task(self, task_name: str):
        self._post("start_task", data={"task_name": task_name})

    def pause_task(self, task_name: str):
        self._post("pause_task", data={"task_name": task_name})

    def run_task(self, task_name: str):
        self._post("run_task", data={"task_name": task_name})
