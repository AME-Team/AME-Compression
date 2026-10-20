"""Tests for the two-pass (target size) video encoding path."""

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from backend import video
from backend.config import COMPRESSION_MODE_TARGET_SIZE, TWO_PASS_FIRST_PASS_SHARE
from backend.models import CompressionStatus, ProgressEvent, VideoCompressionParams
from backend.size_target import MB_IN_BYTES

VIDEO_INFO: dict[str, Any] = {
    "duration": 10.0,
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
}

RunFFmpeg = Callable[
    [list[str], VideoCompressionParams, video.Stats, float, video.PassProgress | None],
    int | None,
]


class FakeFFmpeg:
    """Stand-in for ``video._run_ffmpeg`` recording the commands it receives."""

    def __init__(
        self,
        output: Path | None = None,
        output_size: int = 1024,
        codes: list[int | None] | None = None,
    ) -> None:
        self.calls: list[list[str]] = []
        self.output = output
        self.output_size = output_size
        self.codes = codes or []
        self.progress: list[video.PassProgress | None] = []

    def __call__(
        self,
        cmd: list[str],
        _params: VideoCompressionParams,
        _stats: video.Stats,
        _total_duration: float,
        progress: video.PassProgress | None = None,
    ) -> int | None:
        self.calls.append(cmd)
        self.progress.append(progress)
        index = len(self.calls) - 1
        code = self.codes[index] if index < len(self.codes) else 0
        if code == 0 and self.output is not None and index == len(self.codes) - 1:
            self.output.write_bytes(b"\0" * self.output_size)
        return code


def _touch(tmp_path: Path, name: str, size: int = 4096) -> Path:
    path = tmp_path / name
    path.write_bytes(b"\0" * size)
    return path


def _patch_video_info(monkeypatch: pytest.MonkeyPatch, info: dict[str, Any] | None = None) -> None:
    payload = dict(VIDEO_INFO if info is None else info)

    def fake_info(*_args: Any, **_kwargs: Any) -> dict[str, Any] | None:
        return payload

    monkeypatch.setattr(video, "get_video_info_safe", fake_info)


def _passlog_dirs() -> set[str]:
    root = Path(tempfile.gettempdir())
    return {str(p) for p in root.glob("ame_passlog_*") if p.is_dir()}


class TestTwoPassCommandStructure:
    def test_pass1_is_analysis_only_and_shares_bitrate(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=100 * MB_IN_BYTES)
        output = tmp_path / "out.mp4"
        _patch_video_info(monkeypatch)
        fake = FakeFFmpeg(output=output, output_size=20 * MB_IN_BYTES, codes=[0, 0])
        monkeypatch.setattr(video, "_run_ffmpeg", fake)

        result = video.compress_video_service(
            input_path=str(source),
            output_path=str(output),
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
            target_size_bytes=20 * MB_IN_BYTES,
            preset=6,
        )

        assert result.is_success
        assert len(fake.calls) == 2
        pass1, pass2 = fake.calls

        assert pass1[pass1.index("-pass") + 1] == "1"
        assert pass2[pass2.index("-pass") + 1] == "2"
        passlog1 = pass1[pass1.index("-passlogfile") + 1]
        passlog2 = pass2[pass2.index("-passlogfile") + 1]
        assert passlog1 == passlog2
        # Pass 1 is analysis-only: no audio, output discarded.
        assert "-an" in pass1
        assert pass1[-2:] == ["null", "-"]
        assert "-an" not in pass2
        # Both passes must target the same video bitrate.
        assert pass1[pass1.index("-b:v") + 1] == pass2[pass2.index("-b:v") + 1]
        assert pass2[-1] == str(output)

    def test_filters_are_shared_between_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=100 * MB_IN_BYTES)
        output = tmp_path / "out.mp4"
        _patch_video_info(monkeypatch)
        fake = FakeFFmpeg(output=output, codes=[0, 0])
        monkeypatch.setattr(video, "_run_ffmpeg", fake)

        result = video.compress_video_service(
            input_path=str(source),
            output_path=str(output),
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
            target_size_percent=50.0,
            resolution="1280x720",
            max_fps=24,
        )

        assert result.is_success
        assert result.width == 1280
        assert result.height == 720
        for cmd in fake.calls:
            assert cmd[cmd.index("-vf") + 1] == "scale=1280:720,fps=24"

    def test_passlog_is_removed_after_the_job(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=100 * MB_IN_BYTES)
        _patch_video_info(monkeypatch)
        before = _passlog_dirs()
        fake = FakeFFmpeg(output=tmp_path / "out.mp4", codes=[0, 0])
        monkeypatch.setattr(video, "_run_ffmpeg", fake)

        video.compress_video_service(
            input_path=str(source),
            output_path=str(tmp_path / "out.mp4"),
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
            target_size_percent=50.0,
        )

        assert _passlog_dirs() == before


class TestPassProgress:
    def test_first_pass_maps_into_first_half(self) -> None:
        mapping = video.PassProgress(offset=0.0, span=TWO_PASS_FIRST_PASS_SHARE, index=1, total=2)
        event = mapping.map_event(ProgressEvent(percent=50.0))
        assert event.percent == 25.0
        assert (event.pass_index, event.pass_total) == (1, 2)

    def test_second_pass_maps_into_second_half(self) -> None:
        mapping = video.PassProgress(
            offset=TWO_PASS_FIRST_PASS_SHARE,
            span=100.0 - TWO_PASS_FIRST_PASS_SHARE,
            index=2,
            total=2,
        )
        event = mapping.map_event(ProgressEvent(percent=100.0))
        assert event.percent == 100.0


class TestTwoPassResults:
    def test_success_reports_target_and_overshoot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=20 * MB_IN_BYTES)
        output = tmp_path / "out.mp4"
        _patch_video_info(monkeypatch)
        # 50% of a 20 MB input is a 10 MB target; the fake encoder writes 12 MB.
        fake = FakeFFmpeg(output=output, output_size=12 * MB_IN_BYTES, codes=[0, 0])
        monkeypatch.setattr(video, "_run_ffmpeg", fake)

        result = video.compress_video_service(
            input_path=str(source),
            output_path=str(output),
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
            target_size_percent=50.0,
        )

        assert result.is_success
        assert result.compression_mode == COMPRESSION_MODE_TARGET_SIZE
        assert result.target_size_bytes == 10 * MB_IN_BYTES
        assert result.video_bitrate_kbps > 0
        assert result.target_size_achieved is False

    def test_cancellation_during_pass1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=20 * MB_IN_BYTES)
        _patch_video_info(monkeypatch)
        fake = FakeFFmpeg(codes=[None])
        monkeypatch.setattr(video, "_run_ffmpeg", fake)

        result = video.compress_video_service(
            input_path=str(source),
            output_path=str(tmp_path / "out.mp4"),
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
            target_size_bytes=1 * MB_IN_BYTES,
        )

        assert result.status == CompressionStatus.CANCELLED
        assert len(fake.calls) == 1

    def test_pass1_failure_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=20 * MB_IN_BYTES)
        _patch_video_info(monkeypatch)
        fake = FakeFFmpeg(codes=[3])
        monkeypatch.setattr(video, "_run_ffmpeg", fake)

        result = video.compress_video_service(
            input_path=str(source),
            output_path=str(tmp_path / "out.mp4"),
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
            target_size_percent=50.0,
        )

        assert result.is_failed
        assert "pass 1" in result.error_message

    def test_invalid_target_returns_user_facing_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=20 * MB_IN_BYTES)
        _patch_video_info(monkeypatch)

        result = video.compress_video_service(
            input_path=str(source),
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
        )

        assert result.is_failed
        assert "指定されていません" in result.error_message

    def test_unknown_duration_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=20 * MB_IN_BYTES)
        _patch_video_info(monkeypatch, {**VIDEO_INFO, "duration": 0})

        result = video.compress_video_service(
            input_path=str(source),
            output_path=str(tmp_path / "out.mp4"),
            compression_mode=COMPRESSION_MODE_TARGET_SIZE,
            target_size_percent=50.0,
        )

        assert result.is_failed
        assert "長さを取得できない" in result.error_message

    def test_crf_mode_ignores_target_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        source = _touch(tmp_path, "in.mp4", size=20 * MB_IN_BYTES)
        output = tmp_path / "out.mp4"
        _patch_video_info(monkeypatch)
        fake = FakeFFmpeg(output=output, codes=[0])
        monkeypatch.setattr(video, "_run_ffmpeg", fake)

        result = video.compress_video_service(
            input_path=str(source),
            output_path=str(output),
            target_size_percent=50.0,
        )

        assert result.is_success
        assert len(fake.calls) == 1
        assert "-pass" not in fake.calls[0]
        assert result.target_size_bytes == 0
