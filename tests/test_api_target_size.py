"""API validation tests for the target-size (two-pass) video mode."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from backend.api.app import create_app
from backend.api.job_runner import job_runner
from backend.size_target import MB_IN_BYTES
from flask.testing import FlaskClient


@pytest.fixture
def client(settings_manager: Any) -> Generator[FlaskClient, None, None]:
    _ = settings_manager
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        with job_runner.tasks_lock:
            job_runner.tasks.clear()
        yield client


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    path = tmp_path / "input.mp4"
    path.write_bytes(b"\0" * (10 * MB_IN_BYTES))
    return path


def _post(client: FlaskClient, payload: dict[str, Any]) -> Any:
    return client.post("/api/jobs/video", json=payload)


def test_target_size_requires_one_target(client: FlaskClient, source_file: Path) -> None:
    response = _post(
        client,
        {"input_path": str(source_file), "compression_mode": "target_size"},
    )
    assert response.status_code == 400
    assert "指定されていません" in response.get_json()["error"]


def test_target_size_rejects_both_fields(client: FlaskClient, source_file: Path) -> None:
    response = _post(
        client,
        {
            "input_path": str(source_file),
            "compression_mode": "target_size",
            "target_size_bytes": 5 * MB_IN_BYTES,
            "target_size_percent": 50,
        },
    )
    assert response.status_code == 400
    assert "どちらか一方" in response.get_json()["error"]


def test_target_size_rejects_out_of_range_percent(client: FlaskClient, source_file: Path) -> None:
    response = _post(
        client,
        {
            "input_path": str(source_file),
            "compression_mode": "target_size",
            "target_size_percent": 150,
        },
    )
    assert response.status_code == 400
    assert "範囲" in response.get_json()["error"]


def test_target_size_rejects_too_small_absolute(client: FlaskClient, source_file: Path) -> None:
    response = _post(
        client,
        {
            "input_path": str(source_file),
            "compression_mode": "target_size",
            "target_size_bytes": 10,
        },
    )
    assert response.status_code == 400
    assert "以上" in response.get_json()["error"]


def test_target_fields_require_target_mode(client: FlaskClient, source_file: Path) -> None:
    response = _post(
        client,
        {"input_path": str(source_file), "target_size_percent": 50},
    )
    assert response.status_code == 400
    assert "compression_mode" in response.get_json()["error"]


def test_invalid_mode_is_rejected(client: FlaskClient, source_file: Path) -> None:
    response = _post(
        client,
        {"input_path": str(source_file), "compression_mode": "two-pass-magic"},
    )
    assert response.status_code == 400
    assert "compression_mode" in response.get_json()["error"]


def test_valid_percent_request_is_accepted(
    client: FlaskClient, source_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start = MagicMock(return_value="task-1234")
    monkeypatch.setattr(job_runner, "start_task", start)

    response = _post(
        client,
        {
            "input_path": str(source_file),
            "compression_mode": "target_size",
            "target_size_percent": 40,
        },
    )

    assert response.status_code == 202
    assert response.get_json()["task_id"] == "task-1234"
    kwargs = start.call_args.kwargs
    assert kwargs["compression_mode"] == "target_size"
    assert kwargs["target_size_percent"] == 40.0
    assert kwargs["target_size_bytes"] is None


def test_valid_absolute_request_is_accepted(
    client: FlaskClient, source_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    start = MagicMock(return_value="task-5678")
    monkeypatch.setattr(job_runner, "start_task", start)

    response = _post(
        client,
        {
            "input_path": str(source_file),
            "compression_mode": "target_size",
            "target_size_bytes": 4 * MB_IN_BYTES,
        },
    )

    assert response.status_code == 202
    kwargs = start.call_args.kwargs
    assert kwargs["target_size_bytes"] == 4 * MB_IN_BYTES
    assert kwargs["target_size_percent"] is None
