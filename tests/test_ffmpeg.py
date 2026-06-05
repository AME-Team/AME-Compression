import platform
from pathlib import Path
from unittest.mock import patch

import pytest
from backend.ffmpeg import find_ffmpeg, find_ffprobe, get_ffmpeg_executables


class TestFindFfmpeg:
    def test_finds_system_ffmpeg(self) -> None:
        with patch("backend.ffmpeg._get_bundled_dir") as mock_dir:
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
        with patch("backend.ffmpeg._get_bundled_dir") as mock_dir:
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
