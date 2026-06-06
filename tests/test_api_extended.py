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
        # Clear tasks for clean test
        with job_runner.tasks_lock:
            job_runner.tasks.clear()
        yield client


def test_get_settings(client: FlaskClient) -> None:
    response = client.get("/api/settings")
    assert response.status_code == 200
    assert "language" in response.get_json()
    assert "appearance_mode" in response.get_json()


def test_update_settings(client: FlaskClient) -> None:
    new_settings = {"language": "ja", "appearance_mode": "dark"}
    response = client.post("/api/settings", json=new_settings)
    assert response.status_code == 200
    assert response.get_json()["status"] == "success"

    # Verify changes
    response = client.get("/api/settings")
    assert response.get_json()["language"] == "ja"
    assert response.get_json()["appearance_mode"] == "dark"


def test_audio_compression_endpoint(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
        patch("backend.api.blueprints.jobs.compress_audio_service"),
        patch.object(job_runner, "executor", MagicMock()),
    ):
        response = client.post(
            "/api/jobs/audio", json={"input_path": "test.mp3", "bitrate": "128k"}
        )
        assert response.status_code == 202
        assert "task_id" in response.get_json()


def test_list_jobs(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
        patch("backend.api.blueprints.jobs.compress_video_service"),
        patch.object(job_runner, "executor", MagicMock()),
    ):
        client.post("/api/jobs/video", json={"input_path": "test1.mp4"})
        client.post("/api/jobs/video", json={"input_path": "test2.mp4"})

        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert len(response.get_json()) == 2


def test_get_job_status(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
        patch("backend.api.blueprints.jobs.compress_video_service"),
        patch.object(job_runner, "executor", MagicMock()),
    ):
        resp = client.post("/api/jobs/video", json={"input_path": "test.mp4"})
        task_id = resp.get_json()["task_id"]

        response = client.get(f"/api/jobs/{task_id}")
        assert response.status_code == 200
        assert response.get_json()["id"] == task_id
        assert response.get_json()["status"] == "pending"


def test_get_job_status_not_found(client: FlaskClient) -> None:
    response = client.get("/api/jobs/non-existent-id")
    assert response.status_code == 404


def test_media_info_audio(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.media.Path.exists", return_value=True),
        patch("backend.api.blueprints.media.get_video_info_safe", return_value=None),
        patch(
            "backend.api.blueprints.media.get_audio_info_safe",
            return_value={"bitrate": "128k"},
        ),
    ):
        response = client.get("/api/media/info?path=test.mp3")
        assert response.status_code == 200
        assert response.get_json()["type"] == "audio"
        assert response.get_json()["bitrate"] == "128k"


def test_media_info_not_found(client: FlaskClient) -> None:
    with patch("backend.api.blueprints.media.Path.exists", return_value=False):
        response = client.get("/api/media/info?path=non-existent.mp4")
        assert response.status_code == 404


def test_analyze_volume_endpoint(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.media.Path.exists", return_value=True),
        patch(
            "backend.api.blueprints.media.analyze_volume_level",
            return_value={"mean_volume": -15.0, "max_volume": -1.0},
        ),
    ):
        response = client.post("/api/media/volume-analyze", json={"path": "test.mp4"})
        assert response.status_code == 200
        assert response.get_json()["mean_volume"] == -15.0


def test_analyze_volume_error(client: FlaskClient) -> None:
    with (
        patch("backend.api.blueprints.media.Path.exists", return_value=True),
        patch(
            "backend.api.blueprints.media.analyze_volume_level",
            return_value={"mean_volume": None},
        ),
    ):
        response = client.post("/api/media/volume-analyze", json={"path": "test.mp4"})
        assert response.status_code == 500
        assert "error" in response.get_json()
