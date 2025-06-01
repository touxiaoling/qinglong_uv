import tempfile
import pytest
from fastapi.testclient import TestClient


# 需要配置设置地址
@pytest.fixture(scope="module")
def client():
    from qinglong.main import app

    with tempfile.TemporaryDirectory() as temp_db_dir:
        yield TestClient(app)


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello, Qinglong-uv!"}
    print(response.json())


def test_get_project_list(client: TestClient):
    response = client.get("/api/project_list")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    print(response.json())


def test_get_task_list(client: TestClient):
    response = client.get("/api/task_list")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    print(response.json())
