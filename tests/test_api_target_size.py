"""API validation tests for the target-size (two-pass) video mode."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from backend.api.app import create_app
from backend.api.blueprints import jobs as jobs_blueprint
from backend.api.job_runner import job_runner
from backend.models import VideoCompressionParams
from backend.size_target import MB_IN_BYTES, SizeTarget, TargetSizeError, resolve_target_bitrate
from backend.video import resolve_target_plan
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


def _fake_video_info(
    _video_path: str | Path, _ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Pretend ffprobe reports a 10-minute video."""
    return {"duration": 600.0, "width": 640, "height": 360, "fps": 30.0}


def _no_video_info(
    _video_path: str | Path, _ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Pretend ffprobe cannot read the file."""
    return None


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


def test_target_size_rejects_budget_below_minimum_video_bitrate(
    client: FlaskClient, source_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A target that cannot leave MIN_VIDEO_BITRATE_KBPS must be a 400, not a failed job."""
    monkeypatch.setattr(jobs_blueprint, "get_video_info_safe", _fake_video_info)
    start = MagicMock(return_value="task-should-not-start")
    monkeypatch.setattr(job_runner, "start_task", start)

    response = _post(
        client,
        {
            "input_path": str(source_file),
            "compression_mode": "target_size",
            "target_size_percent": 40,
            "audio_bitrate": "192k",
        },
    )

    with pytest.raises(TargetSizeError) as excinfo:
        resolve_target_bitrate(
            input_size=source_file.stat().st_size,
            duration=600.0,
            audio_bitrate="192k",
            target=SizeTarget(percent=40.0),
            audio_enabled=True,
        )
    assert response.status_code == 400
    assert response.get_json()["error"] == str(excinfo.value)
    start.assert_not_called()
    assert job_runner.tasks == {}


def test_unreadable_media_falls_back_to_job_time_validation(
    client: FlaskClient, source_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed probe must not block the request; the job-level check still runs."""
    monkeypatch.setattr(jobs_blueprint, "get_video_info_safe", _no_video_info)
    start = MagicMock(return_value="task-9999")
    monkeypatch.setattr(job_runner, "start_task", start)

    response = _post(
        client,
        {
            "input_path": str(source_file),
            "compression_mode": "target_size",
            "target_size_percent": 40,
            "audio_bitrate": "192k",
        },
    )

    assert response.status_code == 202
    start.assert_called_once()


def test_job_path_reports_the_same_budget_error(
    client: FlaskClient, source_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The request check and the job-time plan must reject with one message."""
    monkeypatch.setattr(jobs_blueprint, "get_video_info_safe", _fake_video_info)
    monkeypatch.setattr(job_runner, "start_task", MagicMock(return_value="unused"))

    response = _post(
        client,
        {
            "input_path": str(source_file),
            "compression_mode": "target_size",
            "target_size_percent": 40,
            "audio_bitrate": "192k",
        },
    )
    assert response.status_code == 400

    params = VideoCompressionParams(
        input_path=source_file,
        compression_mode="target_size",
        target_size_percent=40.0,
        audio_bitrate="192k",
        audio_enabled=True,
    )
    with pytest.raises(TargetSizeError) as excinfo:
        resolve_target_plan(params, source_file.stat().st_size, 600.0)

    assert response.get_json()["error"] == str(excinfo.value)


def test_plan_is_identical_for_equivalent_audio_inputs() -> None:
    """'192K', '192k' and '192' must all resolve to the same bitrate plan."""
    plans = [
        resolve_target_plan(
            VideoCompressionParams(
                input_path="input.mp4",
                compression_mode="target_size",
                target_size_percent=40.0,
                audio_bitrate=value,
            ),
            100 * MB_IN_BYTES,
            60.0,
        )
        for value in ("192k", "192K", "192")
    ]
    assert len({(plan.audio_kbps, plan.video_kbps) for plan in plans}) == 1
    assert plans[0].audio_kbps == 192
