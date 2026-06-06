from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from backend.api.app import create_app
from backend.api.job_runner import job_runner
from backend.settings import SettingsManager
from flask.testing import FlaskClient


@pytest.fixture
def client(settings_manager: SettingsManager) -> Generator[FlaskClient, None, None]:
    _ = settings_manager
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_api_media_info_endpoint(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.media.Path.exists", return_value=True),
        patch(
            "backend.api.blueprints.media.get_video_info_safe",
            return_value={"width": 1920, "height": 1080},
        ),
    ):
        response = client.get("/api/media/info?path=test.mp4")
        assert response.status_code == 200
        assert response.get_json()["width"] == 1920
        assert response.get_json()["type"] == "video"


def test_start_task_adds_timestamp(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
        patch("backend.api.blueprints.jobs.compress_video_service"),
        patch.object(job_runner, "executor", MagicMock()),
    ):
        # Clear tasks for clean test
        with job_runner.tasks_lock:
            job_runner.tasks.clear()

        response = client.post("/api/jobs/video", json={"input_path": "test.mp4"})
        assert response.status_code == 202
        task_id = response.get_json()["task_id"]

        with job_runner.tasks_lock:
            assert task_id in job_runner.tasks
            assert "created_at" in job_runner.tasks[task_id]
            assert isinstance(job_runner.tasks[task_id]["created_at"], float)


def test_task_completion_adds_finished_at(client: FlaskClient) -> None:
    mock_result = MagicMock()
    mock_result.status.value = "success"
    mock_result.is_success = True
    mock_result.output_path = "out.mp4"
    mock_result.output_size = 1000
    mock_result.compression_ratio = 0.5
    mock_result.error_message = None

    mock_executor = MagicMock()
    with (
        patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
        patch("backend.api.blueprints.jobs.compress_video_service", return_value=mock_result),
        patch.object(job_runner, "executor", mock_executor),
    ):
        with job_runner.tasks_lock:
            job_runner.tasks.clear()

        client.post("/api/jobs/video", json={"input_path": "test.mp4"})

        run_task_func = mock_executor.submit.call_args[0][0]
        run_task_func()

        with job_runner.tasks_lock:
            task_id = next(iter(job_runner.tasks.keys()))
            assert "finished_at" in job_runner.tasks[task_id]
            assert isinstance(job_runner.tasks[task_id]["finished_at"], float)


def test_cancel_task(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
        patch("backend.api.blueprints.jobs.compress_video_service"),
        patch.object(job_runner, "executor", MagicMock()),
    ):
        with job_runner.tasks_lock:
            job_runner.tasks.clear()

        response = client.post("/api/jobs/video", json={"input_path": "test.mp4"})
        task_id = response.get_json()["task_id"]

        response = client.delete(f"/api/jobs/{task_id}")
        assert response.status_code == 200
        assert response.get_json()["status"] == "cancelling"
