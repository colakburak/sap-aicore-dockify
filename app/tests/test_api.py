import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.main.build_and_push_image.delay")
def test_build_image(mock_delay):
    # mock celery task delay method to return dummy task
    dummy_task = MagicMock()
    dummy_task.id = "dummy-task-id"
    mock_delay.return_value = dummy_task

    # mock dockerfile
    dockerfile = b"FROM python:3.9\nRUN pip install requests"
    files = {"dockerfile": ("Dockerfile", dockerfile)}

    # user_name and repo as required params
    params = {"user_name": "test_user", "repo": "test_repo"}

    r = client.post("/build", params=params, files=files)

    # making sure request is successful
    assert r.status_code == 200, r.text
    data = r.json()
    # task_id check
    assert "task_id" in data
    # status check
    assert data["status"] == "Sent to processing queue"
    # image_name check
    assert data["image_reference"] == "test_user/test_repo:latest"


@patch("app.main.AsyncResult")
def test_get_status(mock_async_result):
    # mock result for completed Celery task
    mock_result = MagicMock()
    mock_result.ready.return_value = True
    # result to be a dictionary expected output
    mock_result.result = {
        "status": "success",
        "image_url": "http://example.com/image.tar",
        "image_reference": "test_user/test_repo:latest"
    }
    mock_async_result.return_value = mock_result

    task_id = "FAKE-TEST-TASK-ID"
    response = client.get(f"/status/{task_id}")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "image_url": "http://example.com/image.tar",
        "image_reference": "test_user/test_repo:latest"
    }
