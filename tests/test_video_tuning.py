"""Tests for the SVT-AV1 perceptual tuning and 10-bit encode options."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from backend import video
from backend.api.app import create_app
from backend.api.job_runner import job_runner
from backend.config import (
    COMPRESSION_MODE_TARGET_SIZE,
    DEFAULT_TEN_BIT,
    DEFAULT_VISUAL_TUNING,
    SVT_AV1_VISUAL_TUNING_PARAMS,
)
from backend.models import VideoCompressionResult
from backend.settings import SettingsManager
from flask.testing import FlaskClient

VIDEO_INFO: dict[str, Any] = {"duration": 10.0, "width": 1920, "height": 1080, "fps": 30.0}
TUNING_ARGS = ["-svtav1-params", ":".join(SVT_AV1_VISUAL_TUNING_PARAMS)]


class RecordingFFmpeg:
    """Stand-in for ``video._run_ffmpeg`` that records every command."""

    def __init__(self, output: Path | None, output_size: int = 1024) -> None:
        self.calls: list[list[str]] = []
        self.output = output
        self.output_size = output_size

    def __call__(
        self,
        cmd: list[str],
        _params: Any,
        _stats: Any,
        _total_duration: float,
        _progress: Any = None,
    ) -> int | None:
        self.calls.append(cmd)
        if self.output is not None:
            self.output.write_bytes(b"\0" * self.output_size)
        return 0


def _compress(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_size: int = 4096,
    **kwargs: Any,
) -> tuple[VideoCompressionResult, RecordingFFmpeg]:
    """Run the video service with a fake encoder and return its recording."""
    source = tmp_path / "in.mp4"
    source.write_bytes(b"\0" * source_size)
    output = tmp_path / "out.mp4"
    fake = RecordingFFmpeg(output)

    def fake_info(*_args: Any, **_kwargs: Any) -> dict[str, Any] | None:
        return dict(VIDEO_INFO)

    monkeypatch.setattr(video, "get_video_info_safe", fake_info)
    monkeypatch.setattr(video, "_run_ffmpeg", fake)
    result = video.compress_video_service(input_path=str(source), output_path=str(output), **kwargs)
    return result, fake


class TestVisualTuningArgs:
    def test_defaults_are_perceptual_tuning_on_and_ten_bit_off(self) -> None:
        assert DEFAULT_VISUAL_TUNING is True
        assert DEFAULT_TEN_BIT is False

    def test_crf_command_carries_the_tuning_parameters(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result, fake = _compress(tmp_path, monkeypatch)

        assert result.is_success
        cmd = fake.calls[0]
        offset = cmd.index("-svtav1-params")
        assert cmd[offset : offset + 2] == TUNING_ARGS

    def test_disabling_tuning_omits_the_parameter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result, fake = _compress(tmp_path, monkeypatch, visual_tuning=False)

        assert result.is_success
        assert "-svtav1-params" not in fake.calls[0]

    def test_ten_bit_adds_the_pixel_format(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result, fake = _compress(tmp_path, monkeypatch, ten_bit=True)

        assert result.is_success
        cmd = fake.calls[0]
        offset = cmd.index("-pix_fmt")
        assert cmd[offset : offset + 2] == ["-pix_fmt", "yuv420p10le"]

    def test_ten_bit_off_keeps_the_source_pixel_format(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result, fake = _compress(tmp_path, monkeypatch)

        assert result.is_success
        assert "-pix_fmt" not in fake.calls[0]

    def test_two_pass_uses_the_same_options_in_both_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result, fake = _compress(
            tmp_path,
            monkeypatch,
            source_size=20 * 1024 * 1024,
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
            target_size_percent=50.0,
            ten_bit=True,
        )

        assert result.is_success
        assert len(fake.calls) == 2
        for cmd in fake.calls:
            offset = cmd.index("-svtav1-params")
            assert cmd[offset : offset + 2] == TUNING_ARGS
            offset = cmd.index("-pix_fmt")
            assert cmd[offset : offset + 2] == ["-pix_fmt", "yuv420p10le"]

    def test_result_reports_the_applied_options(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result, _fake = _compress(tmp_path, monkeypatch, visual_tuning=False, ten_bit=True)

        assert result.visual_tuning is False
        assert result.ten_bit is True


@pytest.fixture
def client(settings_manager: SettingsManager) -> Generator[FlaskClient, None, None]:
    _ = settings_manager
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        with job_runner.tasks_lock:
            job_runner.tasks.clear()
        yield client


class TestVideoJobRequest:
    def _post(self, client: FlaskClient, payload: dict[str, Any]) -> tuple[Any, Any]:
        with (
            patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
            patch(
                "backend.api.blueprints.jobs.job_runner.start_task", return_value="task-id"
            ) as start_task,
        ):
            response = client.post("/api/jobs/video", json=payload)
        return response, start_task

    def test_omitted_fields_use_the_defaults(self, client: FlaskClient) -> None:
        response, start_task = self._post(client, {"input_path": "test.mp4"})

        assert response.status_code == 202
        kwargs = start_task.call_args.kwargs
        assert kwargs["visual_tuning"] is True
        assert kwargs["ten_bit"] is False

    def test_explicit_values_are_forwarded(self, client: FlaskClient) -> None:
        response, start_task = self._post(
            client, {"input_path": "test.mp4", "visual_tuning": False, "ten_bit": True}
        )

        assert response.status_code == 202
        kwargs = start_task.call_args.kwargs
        assert kwargs["visual_tuning"] is False
        assert kwargs["ten_bit"] is True

    @pytest.mark.parametrize("field", ["visual_tuning", "ten_bit"])
    def test_non_boolean_is_rejected(self, client: FlaskClient, field: str) -> None:
        response, start_task = self._post(client, {"input_path": "test.mp4", field: "true"})

        assert response.status_code == 400
        assert field in response.get_json()["error"]
        start_task.assert_not_called()

    def test_job_runner_is_reached_only_after_validation(self, client: FlaskClient) -> None:
        # Regression guard: a rejected request must not leave a job behind.
        with (
            patch("backend.api.blueprints.jobs.Path.exists", return_value=True),
            patch.object(job_runner, "executor", MagicMock()),
        ):
            client.post("/api/jobs/video", json={"input_path": "test.mp4", "ten_bit": 1})

        assert job_runner.list_tasks() == []
