import shlex
import sys
from time import monotonic, sleep

from fastapi.testclient import TestClient
from git import Repo

from qinglong.config import settings
from qinglong.web import app


def wait_for(predicate):
    deadline = monotonic() + 5
    while monotonic() < deadline:
        if value := predicate():
            return value
        sleep(0.02)
    raise AssertionError("Task did not reach the expected state.")


def test_project_and_task_workflow_survives_restart(tmp_path):
    repo = Repo.init(tmp_path / "source", mkdir=True)
    config = tmp_path / "source" / "config.yml"
    config.write_text("enabled: true\n")
    repo.index.add([config.name])
    repo.index.commit("Initial configuration")
    project = "/api/projects/test-project"
    task = "/api/tasks/test-task"

    with TestClient(app) as client:
        assert client.post("/api/projects", json={"url": str(config.parent), "name": "test-project"}).status_code == 204
        assert client.post(project + "/pull").status_code == 204
        assert client.get(project + "/config").json() == {"filename": "config.yml", "content": "enabled: true\n"}
        assert client.put(project + "/config", json={"content": "enabled: [\n"}).status_code == 422
        assert client.put(project + "/config", json={"content": "enabled: false\n"}).status_code == 204

        command = f"{shlex.quote(sys._base_executable)} -c \"import time; print('first'); print('second'); time.sleep(60)\""
        data = {"name": "test-task", "project_name": "test-project", "cron": "3600", "command": command}
        created = client.post("/api/tasks", json=data)
        assert created.status_code == 201
        updated = client.put(task, json={"cron": "3600", "command": command, "timeout": 90})
        assert updated.status_code == 200
        assert updated.json()["next_run_at"] == created.json()["next_run_at"]
        assert client.post("/api/tasks", json=data).status_code == 409
        assert client.delete(project).status_code == 409
        assert client.post(task + "/pause").json()["next_run_at"] is None
        assert client.put(task, json={"cron": "invalid", "command": command}).status_code == 422
        assert client.get("/api/tasks").json()[0]["cron"] == "3600"
        quiet_command = f'{shlex.quote(sys._base_executable)} -c "import time; time.sleep(60)"'
        assert client.put(task, json={"cron": "7200", "command": quiet_command}).json()["status"] == "paused"
        assert client.post(task + "/run").status_code == 202
        wait_for(lambda: client.get("/api/tasks").json()[0]["is_running"])

    with TestClient(app) as client:
        [restored] = client.get("/api/tasks").json()
        assert restored["registered"] and restored["status"] == "paused" and restored["next_run_at"] is None
        assert not restored["is_running"]
        assert any("Service shutdown" in line for line in client.get(task + "/logs").json())
        assert client.put(task, json={"cron": restored["cron"], "command": command}).status_code == 200
        assert client.post(task + "/run").status_code == 202
        try:

            def read_output():
                lines = client.get(task + "/logs").json()
                return [line.rsplit("]: ", 1)[-1] for line in lines if line.endswith(("first", "second"))] or None

            assert wait_for(lambda: read_output() == ["first", "second"])
            [running] = client.get("/api/tasks").json()
            assert running["is_running"] and running["status"] == "paused" and running["next_run_at"] is None
            assert client.post(task + "/run").status_code == 409
        finally:
            if client.get("/api/tasks").json()[0]["is_running"]:
                assert client.post(task + "/kill").status_code == 204

        assert client.post(task + "/resume").json()["next_run_at"]
        assert client.delete(task).status_code == 204
        assert client.delete(project).status_code == 204
        assert client.post("/api/sync").status_code == 204
        assert client.get("/api/projects").json() == []
        assert not (settings.PROJECT_PATH / "test-project").exists()
