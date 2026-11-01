import platform
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from backend.ffmpeg import (
    find_ffmpeg,
    find_ffprobe,
    get_ffmpeg_executables,
    get_pix_fmt_bit_depth,
    get_video_stream_details,
)


class TestFindFfmpeg:
    def test_finds_system_ffmpeg(self) -> None:
        with (
            patch("backend.ffmpeg._get_bundled_dir") as mock_dir,
            patch("backend.ffmpeg.shutil.which", return_value="/usr/bin/ffmpeg"),
        ):
            fake_bin = Path("/nonexistent/bundled/dir")
            mock_dir.return_value = fake_bin
            result = find_ffmpeg()
            assert "ffmpeg" in result

    def test_raises_when_not_found(self) -> None:
        with (
            patch("backend.ffmpeg._get_bundled_dir") as mock_dir,
            patch("backend.ffmpeg.shutil.which", return_value=None),
        ):
            fake_bin = Path("/nonexistent/bundled/dir")
            mock_dir.return_value = fake_bin
            with pytest.raises(FileNotFoundError, match="ffmpeg"):
                find_ffmpeg()

    def test_prefers_bundled_over_system(self, tmp_path: Path) -> None:
        is_windows = platform.system() == "Windows"
        ffmpeg_name = "ffmpeg.exe" if is_windows else "ffmpeg"

        bundled_bin = tmp_path / "bin"
        bundled_bin.mkdir()
        (bundled_bin / ffmpeg_name).write_text("fake")

        with patch("backend.ffmpeg._get_bundled_dir", return_value=bundled_bin):
            result = find_ffmpeg()
            assert str(bundled_bin / ffmpeg_name) == result


class TestFindFfprobe:
    def test_finds_system_ffprobe(self) -> None:
        with (
            patch("backend.ffmpeg._get_bundled_dir") as mock_dir,
            patch("backend.ffmpeg.shutil.which", return_value="/usr/bin/ffprobe"),
        ):
            fake_bin = Path("/nonexistent/bundled/dir")
            mock_dir.return_value = fake_bin
            result = find_ffprobe()
            assert "ffprobe" in result

    def test_raises_when_not_found(self) -> None:
        with (
            patch("backend.ffmpeg._get_bundled_dir") as mock_dir,
            patch("backend.ffmpeg.shutil.which", return_value=None),
        ):
            fake_bin = Path("/nonexistent/bundled/dir")
            mock_dir.return_value = fake_bin
            with pytest.raises(FileNotFoundError, match="ffprobe"):
                find_ffprobe()

    def test_prefers_bundled_over_system(self, tmp_path: Path) -> None:
        is_windows = platform.system() == "Windows"
        ffprobe_name = "ffprobe.exe" if is_windows else "ffprobe"

        bundled_bin = tmp_path / "bin"
        bundled_bin.mkdir()
        (bundled_bin / ffprobe_name).write_text("fake")

        with patch("backend.ffmpeg._get_bundled_dir", return_value=bundled_bin):
            result = find_ffprobe()
            assert str(bundled_bin / ffprobe_name) == result


class TestGetFfmpegExecutables:
    def test_returns_tuple(self) -> None:
        result = get_ffmpeg_executables()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_strings(self) -> None:
        ffmpeg, ffprobe = get_ffmpeg_executables()
        assert isinstance(ffmpeg, str)
        assert isinstance(ffprobe, str)

    def test_fallback_to_system(self) -> None:
        ffmpeg, ffprobe = get_ffmpeg_executables()
        assert "ffmpeg" in ffmpeg
        assert "ffprobe" in ffprobe

    def test_fallback_on_not_found(self) -> None:
        with (
            patch("backend.ffmpeg.find_ffmpeg", side_effect=FileNotFoundError),
            patch("backend.ffmpeg.find_ffprobe", side_effect=FileNotFoundError),
        ):
            ffmpeg, ffprobe = get_ffmpeg_executables()
            assert ffmpeg == "ffmpeg"
            assert ffprobe == "ffprobe"


class TestPixelFormatBitDepth:
    def test_known_formats(self) -> None:
        assert get_pix_fmt_bit_depth("yuv420p") == 8
        assert get_pix_fmt_bit_depth("nv12") == 8
        assert get_pix_fmt_bit_depth("yuvj420p") == 8
        assert get_pix_fmt_bit_depth("yuv420p10le") == 10
        assert get_pix_fmt_bit_depth("p010le") == 10
        assert get_pix_fmt_bit_depth("yuv444p12le") == 12
        assert get_pix_fmt_bit_depth("grayf32le") == 32
        # Packed formats carry no p/f suffix and are covered by the lookup table.
        assert get_pix_fmt_bit_depth("x2rgb10le") == 10
        assert get_pix_fmt_bit_depth("xv36le") == 12
        # Semi-planar names end in three digits: p210 is 10-bit, not 210.
        assert get_pix_fmt_bit_depth("p210le") == 10
        assert get_pix_fmt_bit_depth("p410le") == 10
        assert get_pix_fmt_bit_depth("p216le") == 16
        assert get_pix_fmt_bit_depth("v210") == 10
        assert get_pix_fmt_bit_depth("r210") == 10
        assert get_pix_fmt_bit_depth("gray16le") == 16
        # Bare names mirror their le/be twins.
        assert get_pix_fmt_bit_depth("p010") == 10
        assert get_pix_fmt_bit_depth("p016") == 16
        assert get_pix_fmt_bit_depth("p210") == 10

    def test_missing_format(self) -> None:
        assert get_pix_fmt_bit_depth(None) is None
        assert get_pix_fmt_bit_depth("") is None


def _details_payload(stream: dict[str, Any], fmt: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "streams": [{"codec_type": "video", **stream}],
        "format": fmt if fmt is not None else {},
    }


class TestVideoStreamDetails:
    def test_uses_the_stream_bit_rate(self, tmp_path: Path) -> None:
        payload = _details_payload(
            {
                "width": 3840,
                "height": 2160,
                "r_frame_rate": "30000/1001",
                "bit_rate": "5000000",
                "pix_fmt": "yuv420p10le",
                "codec_name": "av1",
            },
            {"bit_rate": "5200000", "duration": "10.0"},
        )
        with patch("backend.ffmpeg.get_detailed_media_info", return_value=payload):
            details = get_video_stream_details(tmp_path / "in.mp4")

        assert details is not None
        assert details["width"] == 3840
        assert details["height"] == 2160
        fps = details["fps"]
        assert isinstance(fps, float)
        assert abs(fps - 29.97) < 0.01
        assert details["duration"] == 10.0
        assert details["bit_rate"] == 5_000_000
        assert details["bit_rate_estimated"] is False
        assert details["bit_depth"] == 10
        assert details["pix_fmt"] == "yuv420p10le"
        assert details["codec_name"] == "av1"

    def test_falls_back_to_the_container_bit_rate(self, tmp_path: Path) -> None:
        payload = _details_payload({"pix_fmt": "yuv420p"}, {"bit_rate": "2500000"})
        with patch("backend.ffmpeg.get_detailed_media_info", return_value=payload):
            details = get_video_stream_details(tmp_path / "in.mkv")

        assert details is not None
        assert details["bit_rate"] == 2_500_000
        assert details["bit_rate_estimated"] is True
        assert details["bit_depth"] == 8

    def test_estimates_from_file_size_when_no_bit_rate_is_stored(self, tmp_path: Path) -> None:
        source = tmp_path / "in.mkv"
        source.write_bytes(b"\0" * 1_000_000)
        payload = _details_payload({"pix_fmt": "yuv420p"}, {"duration": "8.0"})
        with patch("backend.ffmpeg.get_detailed_media_info", return_value=payload):
            details = get_video_stream_details(source)

        assert details is not None
        assert details["bit_rate"] == 1_000_000
        assert details["bit_rate_estimated"] is True

    def test_prefers_bits_per_raw_sample(self, tmp_path: Path) -> None:
        payload = _details_payload(
            {"pix_fmt": "yuv420p", "bits_per_raw_sample": "10", "bit_rate": "1000"}
        )
        with patch("backend.ffmpeg.get_detailed_media_info", return_value=payload):
            details = get_video_stream_details(tmp_path / "in.mp4")

        assert details is not None
        assert details["bit_depth"] == 10

    def test_accepts_a_numeric_bits_per_raw_sample(self, tmp_path: Path) -> None:
        payload = _details_payload(
            {"pix_fmt": "yuv420p", "bits_per_raw_sample": 10, "bit_rate": "1000"}
        )
        with patch("backend.ffmpeg.get_detailed_media_info", return_value=payload):
            details = get_video_stream_details(tmp_path / "in.mp4")

        assert details is not None
        assert details["bit_depth"] == 10

    def test_returns_none_without_a_video_stream(self, tmp_path: Path) -> None:
        payload: dict[str, Any] = {"streams": [{"codec_type": "audio"}], "format": {}}
        with patch("backend.ffmpeg.get_detailed_media_info", return_value=payload):
            assert get_video_stream_details(tmp_path / "in.mp3") is None

    def test_returns_none_when_the_probe_fails(self, tmp_path: Path) -> None:
        with patch("backend.ffmpeg.get_detailed_media_info", return_value=None):
            assert get_video_stream_details(tmp_path / "broken.mp4") is None
