import pytest
import docker
from unittest.mock import patch, MagicMock

from app.tasks import build_and_push_image
from app.tasks_utils import build_image, push_image

@pytest.fixture
def mock_docker_client():
    """Fixture to mock Docker client."""
    with patch("docker.from_env") as mock_client:
        yield mock_client.return_value

def test_build_image(mock_docker_client):
    """Test build_image function."""
    # mock Docker client
    mock_docker_client.images.build.return_value = [MagicMock(id="test_id", tags=["test_user/test_repo:latest"])]

    dockerfile_content = b"FROM python:3.9\nRUN pip install requests"
    optional_files = {"requirements.txt": b"requests\nnumpy"}

    image_reference = build_image(mock_docker_client, "test_user/test_repo:latest", dockerfile_content, optional_files)

    # Assertions
    mock_docker_client.images.build.assert_called_once()
    assert image_reference == "test_user/test_repo:latest"

def test_push_image(mock_docker_client):
    """Test push_image function."""
    mock_docker_client.images.push.return_value = [{"status": "Pushed"}]

    image_reference = push_image(mock_docker_client, "test_user/test_repo:latest")

    # Assertions
    mock_docker_client.images.push.assert_called_once_with("test_user/test_repo:latest", stream=True, decode=True)
    assert image_reference == "test_user/test_repo:latest"

@patch("app.tasks.build_image")
@patch("app.tasks.push_image")
@patch("docker.from_env")
def test_build_and_push_image(mock_docker_from_env, mock_push_image, mock_build_image):
    """Test build_and_push_image Celery task."""

    # Mock Docker client
    mock_docker_client = MagicMock()
    mock_docker_from_env.return_value = mock_docker_client


    mock_build_image.return_value = "test_user/test_repo:latest"
    mock_push_image.return_value = "test_user/test_repo:latest"

    dockerfile_content = b"FROM python:3.9\nRUN pip install requests"
    optional_files = {"requirements.txt": b"requests\nnumpy"}

    result = build_and_push_image("test_user", "test_repo", "latest", dockerfile_content, optional_files)

    # Assertions
    mock_build_image.assert_called_once_with(
        docker.from_env(), "test_user/test_repo:latest", dockerfile_content, optional_files
    )
    mock_push_image.assert_called_once_with(docker.from_env(), "test_user/test_repo:latest")
    
    assert result["image_reference"] == "test_user/test_repo:latest"
    assert result["image_url"] == "https://hub.docker.com/r/test_user/test_repo"
