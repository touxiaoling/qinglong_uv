import shlex
import sys
from time import monotonic, sleep

from fastapi.testclient import TestClient
from git import Repo

from qinglong import notify
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
        assert restored["latest_run"]["status"] == "interrupted"
        assert restored["latest_run"]["source"] == "manual"
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


def test_run_history_tracks_timeout_overlap_and_revision(tmp_path):
    repo = Repo.init(tmp_path / "source", mkdir=True)
    commit = repo.index.commit("Initial commit")
    command = f'{shlex.quote(sys._base_executable)} -c "import time; print(123); time.sleep(60)"'
    path = "/api/tasks/history-task"
    with TestClient(app) as client:
        assert client.post("/api/projects", json={"url": repo.working_dir, "name": "history-project"}).status_code == 204
        revision = client.get("/api/projects/history-project/revision").json()
        assert revision == {"branch": repo.active_branch.name, "commit": commit.hexsha}
        created = client.post(
            "/api/tasks",
            json={
                "name": "history-task",
                "project_name": "history-project",
                "cron": "1",
                "command": command,
                "timeout": 3,
            },
        )
        assert created.status_code == 201
        assert created.json()["latest_run"] is None

        def find_status(status):
            return next((run for run in client.get(path + "/runs").json() if run["status"] == status), None)

        skipped = wait_for(lambda: find_status("skipped"))
        assert skipped["source"] == "scheduled"
        assert skipped["reason"] == "Previous run still active"
        assert skipped["started_at"] is None
        assert client.post(path + "/pause").status_code == 200
        timed_out = wait_for(lambda: find_status("timed_out"))
        assert timed_out["scheduled_at"] <= timed_out["started_at"] <= timed_out["finished_at"]
        assert timed_out["commit"] == commit.hexsha
        stored = client.get(f"{path}/runs/{timed_out['id']}").json()
        assert "123" in stored["output"]
        assert "Timed out after 3s" in stored["output"]

    with TestClient(app) as client:
        assert client.get(f"{path}/runs/{timed_out['id']}").json() == stored


def test_failure_webhook_is_opt_in_and_groups_repeated_failures(tmp_path, monkeypatch):
    sent = []

    def post(url, *, json, timeout):
        assert url == "http://webhook.test/"
        sent.append(json)
        return notify.httpx2.Response(200, request=notify.httpx2.Request("POST", url))

    monkeypatch.setattr(settings, "NOTIFY_WEBHOOK_URL", "http://webhook.test/")
    monkeypatch.setattr(settings, "PANEL_PUBLIC_URL", "http://panel.test")
    monkeypatch.setattr(notify.httpx2, "post", post)
    repo = Repo.init(tmp_path / "source", mkdir=True)
    repo.index.commit("Initial commit")
    path = "/api/tasks/alerts-task"
    executable = shlex.quote(sys._base_executable)
    failure = f'{executable} -c "raise SystemExit(2)"'
    success = f'{executable} -c "print(456)"'
    expected = ["failed", "still_failing", "recovered"]
    with TestClient(app) as client:
        assert client.post("/api/projects", json={"url": repo.working_dir, "name": "alerts-project"}).status_code == 204
        data = {"name": "alerts-task", "project_name": "alerts-project", "cron": "3600", "command": failure}
        assert client.post("/api/tasks", json=data).status_code == 201

        def run_once():
            count = len(client.get(path + "/runs").json())
            response = wait_for(lambda: (result := client.post(path + "/run")).status_code != 409 and result)
            assert response.status_code == 202

            def completed():
                runs = client.get(path + "/runs").json()
                if len(runs) > count and runs[0]["status"] != "running":
                    return runs[0]

            return wait_for(completed)

        assert run_once()["exit_code"] == 2
        assert not sent
        assert client.put(path, json={**data, "notify_on_failure": True}).status_code == 200
        failed, _, repeated, _ = [run_once() for _ in range(4)]
        assert client.put(path, json={**data, "command": success}).status_code == 200
        recovered = run_once()
        wait_for(lambda: len(sent) == 3)
        assert [event["event"] for event in sent] == expected
        assert [event["run_id"] for event in sent] == [failed["id"], repeated["id"], recovered["id"]]
        assert sent[-1]["run_url"] == f"http://panel.test/?task=alerts-task&run={recovered['id']}"
        assert "456" in client.get(f"{path}/runs/{recovered['id']}").json()["output"]
        assert "456" not in client.get(f"{path}/runs/{failed['id']}").json()["output"]
